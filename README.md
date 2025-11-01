# Photo Manager

A lightweight, self-contained photo management application built with FastAPI and Alpine.js. Designed for single-user management of 10k-50k photos with a minimal, dark-themed UI.

## Features

- 📁 **Folder-based organization** - Browse photos in hierarchical folder structure
- 📸 **Photo viewing** - Lightbox viewer with keyboard navigation
- 🏷️ **Albums & Tags** - Virtual organization with many-to-many relationships
- 🔍 **Search & filter** - Find photos by filename, tags, albums, and dates
- 📊 **EXIF metadata** - View camera settings, lens info, GPS data
- 🖼️ **RAW support** - View CR2, NEF, DNG, ARF, and other RAW formats
- ♻️ **Recycle bin** - Soft delete with restore functionality
- ⏮️ **Rollback system** - Undo any actions with point-in-time rollback
- 🔄 **Auto-detection** - Filesystem watcher for new photos
- 🎨 **Dark theme** - Minimalist UI focused on photos

## Tech Stack

- **Backend**: Python 3.13, FastAPI, SQLite, Pillow
- **Frontend**: Alpine.js, Tailwind CSS (zero build tools)
- **Storage**: Content-addressable (SHA256) for deduplication
- **Deploy**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- A directory containing your photos

### Setup

1. **Clone the repository**
   ```bash
   cd photo_manager
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults are fine for most users)
   ```

3. **Mount your photos directory**

   Edit `docker-compose.yml` and update the photos volume path:
   ```yaml
   volumes:
     - /path/to/your/photos:/photos:rw
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Access the application**
   ```
   Open http://localhost:8000
   ```

   The initial scan will run automatically and index your photos.

### Stopping the Application

```bash
docker-compose down
```

### Viewing Logs

```bash
docker-compose logs -f
```

## Usage

### Browsing Photos

- Click folders in the left sidebar to navigate your photo library
- Photos are displayed in a grid sorted alphabetically
- Click any photo to open the lightbox viewer
- Use arrow keys to navigate between photos in the lightbox

### Albums

- Create albums to organize photos virtually (without moving files)
- Click "+" next to "Albums" to create a new album
- Photos can belong to multiple albums

### Tags

- Tag photos with custom labels for easy filtering
- Click "+" next to "Tags" to create a new tag
- Use tags in combination with search

### Search

- Search by filename in the top search bar
- Filter by tags, albums, and date ranges using the search API

### File Operations

- **Move**: Move photos between folders (updates filesystem)
- **Rename**: Rename photo files (updates filesystem)
- **Delete**: Soft delete to recycle bin (can be restored)

### Recycle Bin

- View deleted photos in the "Recycle Bin" section
- Restore photos to their original location or "Restored" folder
- Photos found in recycle bin during scan are automatically visible
- Permanently delete or empty the entire bin

### Rollback System

- Complete action history with automatic tracking via SQLite triggers
- Rollback to any point in time with a single click
- Undo complex operations like bulk moves, deletions, or tag changes
- View action log in sidebar with timestamp and description
- System keeps last 1000 actions for rollback

### Scanning

- Click "Scan Library" to detect new photos added to the filesystem
- Auto-watch is enabled by default (new photos detected automatically)
- Duplicates (same content hash) are automatically skipped during scanning

## Configuration

Edit `.env` or environment variables in `docker-compose.yml`:

```bash
# Paths
PHOTOS_PATH=/photos                           # Photos directory (inside container)
DATABASE_PATH=/app/data/metadata/photos.db    # SQLite database
THUMBNAIL_PATH=/app/data/cache/thumbnails     # Thumbnail cache
# Note: Deleted photos use soft-delete (deleted_at timestamp in DB)

# Performance
THUMBNAIL_SIZE=300                            # Thumbnail max dimension (px)
THUMBNAIL_QUALITY=85                          # JPEG quality (1-100)
SCAN_ON_STARTUP=true                          # Run scan on startup
AUTO_WATCH=true                               # Auto-detect new photos

# Action Log
ACTION_LOG_MAX_RECORDS=1000                   # Number of rollback actions to keep
```

## API Documentation

FastAPI provides interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `GET /api/photos` - List photos (paginated)
- `GET /api/folders` - Get folder tree
- `GET /api/albums` - List albums
- `GET /api/tags` - List tags
- `GET /api/search` - Search photos
- `POST /api/photos/scan` - Trigger library scan
- `GET /api/recycle-bin` - List deleted photos
- `GET /api/action-log` - View action history
- `POST /api/action-log/rollback` - Rollback to timestamp
- `GET /api/stats` - Library statistics

## Development

### Running Without Docker

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export PHOTOS_PATH=/path/to/your/photos
   export DATABASE_PATH=./data/metadata/photos.db
   export THUMBNAIL_PATH=./data/cache/thumbnails
   # Recycle bin uses soft-delete in database, no directory needed
   ```

4. **Run the application**
   ```bash
   uvicorn backend.main:app --reload
   ```

### Project Structure

```
photo-manager/
├── backend/               # Python backend
│   ├── api/              # FastAPI endpoints
│   ├── models/           # Pydantic models
│   ├── services/         # Business logic
│   ├── utils/            # Utilities
│   ├── config.py         # Configuration
│   ├── database.py       # Database schema
│   └── main.py           # FastAPI app
├── frontend/             # Frontend assets
│   ├── static/           # Static files
│   │   ├── css/
│   │   ├── js/
│   │   └── icons/
│   └── templates/        # HTML templates
├── data/                 # Persistent data (Docker volume)
├── photos/               # Your photos (mounted)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Features in Detail

### Content-Addressable Storage

Photos are identified by SHA256 hash of their content:
- Survives file moves and renames
- Automatic duplicate detection
- Thumbnails never need regeneration

### Rollback Architecture

The rollback system uses SQLite triggers for automatic action logging:
- **13 triggers** monitor all user actions (albums, tags, photos, moves, deletions)
- **Single photos table** - Recycle bin uses `original_path` column (no separate table)
- **Optimized storage** - Keeps last 1000 actions, automatic cleanup
- **Point-in-time restoration** - Rollback executes inverse operations in reverse order
- **No performance overhead** - Triggers fire only on actual data changes

### RAW Photo Support

Supported formats: CR2, CR3, NEF, ARF, DNG, ORF, RW2, ARW

- Extracts embedded JPEG preview when available (fast)
- Falls back to rendering RAW data (slower but works for all formats)
- View-only (no editing capabilities)

### Filesystem Watcher

- Monitors `/photos` directory for changes
- Auto-indexes new photos within seconds
- Handles external modifications and deletions
- Debounces rapid file additions

### Pagination

- Default: 50 photos per page
- Configurable via API query parameters
- Smooth navigation with previous/next buttons

## Limitations

- **Single user only** - No authentication or multi-user support
- **Photos only** - No video support
- **Simple search** - Filename only (no full-text EXIF search)
- **No upload** - Manages existing photos only
- **External deletions** - Hard deleted (not moved to recycle bin)
- **RAW thumbnails** - Slower to generate (1-3 seconds vs <500ms for JPEG)

## Troubleshooting

### Photos not showing up

- Check that photos directory is correctly mounted in `docker-compose.yml`
- Run "Scan Library" to index photos
- Check logs: `docker-compose logs -f`

### Thumbnails not generating

- Ensure libraw is installed (included in Dockerfile)
- Check thumbnail cache directory permissions
- Look for errors in logs

### Database errors

- Ensure data directory has write permissions
- Check available disk space
- Restart container: `docker-compose restart`

### Performance issues

- Reduce page size in API calls
- Disable auto-watch if not needed: `AUTO_WATCH=false`
- Optimize thumbnail size: `THUMBNAIL_SIZE=200`

## Contributing

This is a single-user photo management tool designed for simplicity.

For feature requests or bug reports, please open an issue.

## License

MIT License - See SPECIFICATIONS.md for full project details

## Acknowledgments

- **FastAPI** - Modern Python web framework
- **Alpine.js** - Lightweight reactive framework
- **Tailwind CSS** - Utility-first CSS framework
- **Pillow** - Python imaging library
- **rawpy** - RAW image processing
