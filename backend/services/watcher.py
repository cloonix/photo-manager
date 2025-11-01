"""Filesystem watcher service for auto-detecting photo changes."""

import time
from pathlib import Path
from threading import Thread
from typing import Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from backend.config import config
from backend.database import get_db
from backend.services.scanner import index_photo
from backend.utils.hashing import compute_file_hash


class PhotoEventHandler(FileSystemEventHandler):
    """Handler for filesystem events in the photos directory."""

    def __init__(self):
        super().__init__()
        self.pending_files: Set[Path] = set()
        self.last_event_time = time.time()

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if file is a supported photo format
        if file_path.suffix.lower() in config.SUPPORTED_FORMATS:
            self.pending_files.add(file_path)
            self.last_event_time = time.time()
            print(f"Detected new photo: {file_path}")

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # If file content changes, treat as new photo with new hash
        if file_path.suffix.lower() in config.SUPPORTED_FORMATS:
            try:
                new_hash = compute_file_hash(file_path)

                # Check if hash changed (different content)
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT id FROM photos WHERE file_path = ?",
                        (str(file_path.relative_to(config.PHOTOS_PATH)),)
                    )
                    row = cursor.fetchone()

                    if row and row["id"] != new_hash:
                        # Content changed, delete old record and re-index
                        cursor.execute("DELETE FROM photos WHERE id = ?", (row["id"],))
                        conn.commit()
                        self.pending_files.add(file_path)
                        self.last_event_time = time.time()
                        print(f"Photo modified (content changed): {file_path}")

            except Exception as e:
                print(f"Error handling modification of {file_path}: {e}")

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Remove from database (hard delete for external deletions)
        if file_path.suffix.lower() in config.SUPPORTED_FORMATS:
            try:
                with get_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "DELETE FROM photos WHERE file_path = ?",
                        (str(file_path.relative_to(config.PHOTOS_PATH)),)
                    )
                    conn.commit()
                    print(f"Photo deleted externally: {file_path}")

            except Exception as e:
                print(f"Error handling deletion of {file_path}: {e}")

    def process_pending_files(self):
        """Process pending files after debounce period."""
        # Wait 1 second after last event
        if time.time() - self.last_event_time < 1.0:
            return

        if not self.pending_files:
            return

        # Process all pending files
        files_to_process = list(self.pending_files)
        self.pending_files.clear()

        for file_path in files_to_process:
            try:
                if file_path.exists():
                    index_photo(file_path)
                    print(f"Indexed: {file_path}")
            except Exception as e:
                print(f"Error indexing {file_path}: {e}")


class PhotoWatcher:
    """Filesystem watcher for the photos directory."""

    def __init__(self):
        self.observer = Observer()
        self.event_handler = PhotoEventHandler()
        self.is_running = False

    def start(self):
        """Start watching the photos directory."""
        if self.is_running:
            return

        print(f"Starting filesystem watcher on {config.PHOTOS_PATH}")

        # Schedule observer
        self.observer.schedule(
            self.event_handler,
            str(config.PHOTOS_PATH),
            recursive=True
        )

        # Start observer thread
        self.observer.start()
        self.is_running = True

        # Start processing thread for pending files
        processing_thread = Thread(target=self._process_loop, daemon=True)
        processing_thread.start()

    def stop(self):
        """Stop watching the photos directory."""
        if not self.is_running:
            return

        print("Stopping filesystem watcher")
        self.observer.stop()
        self.observer.join()
        self.is_running = False

    def _process_loop(self):
        """Background loop to process pending files."""
        while self.is_running:
            try:
                self.event_handler.process_pending_files()
            except Exception as e:
                print(f"Error in processing loop: {e}")

            time.sleep(0.5)


# Global watcher instance
_watcher: PhotoWatcher = None


def start_watcher():
    """Start the global filesystem watcher."""
    global _watcher

    if _watcher is None:
        _watcher = PhotoWatcher()

    _watcher.start()


def stop_watcher():
    """Stop the global filesystem watcher."""
    global _watcher

    if _watcher is not None:
        _watcher.stop()
