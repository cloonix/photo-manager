
# Photo Manager - AI Coding Agent Specification

## Project Summary

Build a lightweight, self-contained photo manager in Docker for single-user managing 10k-50k photos.
__Core Philosophy__: Minimal dependencies, no build tools, maximum simplicity.

__Tech Stack__:

- Backend: Python 3.13 + FastAPI + SQLite + Pillow (5 packages)
- Frontend: Alpine.js + Tailwind CSS (vanilla JS, 0 npm packages, no build step)
- Storage: SQLite database
- Deploy: Docker + Docker Compose

## Recent Major Enhancements

This specification has been updated to reflect significant UX improvements made to the photo manager:

### 🎯 Key Features Added (Since commit 5e67cf7)
1. **Drag-and-Drop Workflow**: Intuitive drag photos to folders, albums, and tags
2. **Enhanced Navigation**: Breadcrumbs, browse-up button, and folder icons in gallery
3. **Quick Album/Tag Management**: Modal dialogs for batch add/remove operations
4. **High-Quality Lightbox**: Separate 1200px preview images (vs 200px thumbnails)
5. **Improved Restore**: Conflict resolution when restoring deleted photos
6. **Better Folder Queries**: Non-recursive SQL for showing only direct children
7. **8-Column Grid**: Higher density gallery (was 5 columns)
8. **Latest Dependencies**: All packages updated to 2025 versions
9. **Rollback System**: Point-in-time rollback with automatic action logging via SQLite triggers

### 📊 Impact
- **Better UX**: Drag-and-drop reduces clicks needed for common operations
- **Faster Navigation**: Breadcrumbs and browse-up make hierarchy traversal instant
- **Higher Quality**: Lightbox now shows full-quality previews instead of tiny thumbnails
- **More Visible**: 8-column grid shows 60% more photos per screen
- **More Reliable**: Restore handles edge cases (file conflicts, duplicate prevention)
- **Safer Operations**: Rollback system allows undoing mistakes with point-in-time recovery

See "Recent Enhancements" section at the end of this document for complete details.

## Core Requirements

### Functional Requirements

1. __Browse photos__ in folder structure with thumbnails
2. __Persistent folder tree view__ (always visible sidebar)
3. Handle __existing photos__ in folder structure
4. __Auto-detect new photos__ added to filesystem (watch folders)
5. __Create folders__ for organizing photos
6. Physically __move/rename/delete__ photos via UI buttons and drag-and-drop
7. Virtually __organize__ photos into albums (many-to-many)
8. __Tag__ photos with custom tags (many-to-many)
9. __Search & filter__ by tags, albums, dates, filename
10. __View EXIF data__ (camera, date, dimensions)
11. __Lightbox viewer__ for photo viewing with high-quality previews
12. __Drag-and-drop__ photos to folders, albums, and tags
13. __Quick add/remove__ photos to/from multiple albums and tags via modal interface
14. __Breadcrumb navigation__ for hierarchical folder browsing
15. __Folder icons in gallery__ showing subfolders with photo counts
16. __Restore deleted photos__ from recycle bin with conflict resolution
17. __Rollback system__ with automatic action logging and point-in-time recovery

### Non-Functional Requirements

- Handle 20,000 photos efficiently
- Single concurrent user
- Gallery loads <2s for 1000 photos
- Thumbnail generation <500ms per image (RAW may take longer)
- Data persists across container restarts
- Zero npm dependencies (no build tools)
- Photo formats: JPEG, PNG, GIF, WebP, RAW (CR2, NEF, ARF, DNG, etc.)
- Lean dark UI design (minimalist, focus on photos)

## Technology Decisions

### Why These Choices?

__SQLite__: File-based, zero config, ACID transactions, perfect for single user
__Alpine.js__: 15KB, reactive UI, no build step, edit & refresh workflow
__FastAPI__: Auto API docs, async support, serves static files directly
__Content Hash IDs__: Photos identified by SHA256, survives file moves
__RAW Support__: Extract embedded JPEG preview or render to JPEG for viewing
__Photos Only__: Skip video complexity, focus on core photo management

## UI/UX Design

### Design Philosophy

__Dark & Lean__: Minimalist interface that puts photos first, reduces eye strain, and eliminates visual clutter.

### Color Palette (Tailwind Dark Theme)

- __Background__: `bg-gray-900` (#111827) - Deep dark background
- __Surface__: `bg-gray-800` (#1f2937) - Cards, modals, panels
- __Border__: `border-gray-700` (#374151) - Subtle dividers
- __Text Primary__: `text-gray-100` (#f3f4f6) - Main text
- __Text Secondary__: `text-gray-400` (#9ca3af) - Metadata, labels
- __Accent__: `bg-blue-600` (#2563eb) - Buttons, links, active states
- __Accent Hover__: `hover:bg-blue-700` (#1d4ed8) - Interactive hover
- __Success__: `text-green-400` - Confirmations
- __Danger__: `text-red-400` - Delete, warnings
- __Muted__: `bg-gray-800/50` - Overlays, lightbox backgrounds

### Design Principles

1. __Photo-First__: Large thumbnails, minimal chrome, photos are the focus
2. __Folder-First Navigation__: Always-visible folder tree sidebar (primary organization method)
3. __Breathing Room__: Generous spacing between elements (p-6, gap-4)
4. __Subtle Interactions__: Smooth transitions, hover states, no jarring animations
5. __Information Hierarchy__: Clear visual distinction between primary and secondary content
6. __Icon-Driven__: Use Feather icons for actions, minimal text labels
7. __Consistent Spacing__: Tailwind spacing scale (4px increments)
8. __No Shadows__: Flat design with borders instead of drop shadows
9. __Monochrome Base__: Grayscale palette with single accent color

### Layout Structure

__Layout Components__:

- __Left Sidebar__: Fixed width (w-64 = 256px), full height, scrollable folder tree, always visible
- __Main Content__: Flexible width, photo grid with pagination
- __Header__: Full width, search bar and action buttons
- __Folder Tree__: Collapsible/expandable folders, indent for nesting levels
- __Albums/Tags Section__: Below folder tree in sidebar

### Component Styles

- __Layout Container__: `flex h-screen bg-gray-900`
- __Sidebar__: `w-64 bg-gray-800 border-r border-gray-700 overflow-y-auto flex-shrink-0` - Always visible
- __Folder Tree__:
  - Folder item: `px-3 py-2 hover:bg-gray-700 cursor-pointer rounded transition`
  - Active folder: `bg-gray-700 text-blue-400`
  - Nested indent: `pl-6, pl-9, pl-12` (increasing indent levels)
  - Folder icon: Feather `folder` or `chevron-right/down` for expand/collapse
  - Create folder button: `text-xs text-gray-400 hover:text-gray-100`
- __Albums/Tags Section__:
  - Section header: `px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide mt-6`
  - Item: `px-3 py-2 hover:bg-gray-700 cursor-pointer rounded text-sm`
- __Main Content__: `flex-1 flex flex-col overflow-hidden`
- __Header Bar__: `bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center gap-4`
- __Gallery Grid__: `grid grid-cols-8 gap-4 p-6 overflow-y-auto` - High-density photo grid (8 columns for more photos per row)
- __Thumbnails__: `rounded-lg overflow-hidden border border-gray-700 hover:border-gray-600 transition` - Clean photo cards
- __Buttons__: `px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition`
- __Inputs__: `bg-gray-800 border border-gray-700 text-gray-100 rounded-lg focus:ring-2 focus:ring-blue-600 px-3 py-2`
- __Modals__: `bg-gray-800 border border-gray-700 rounded-xl shadow-2xl` - Elevated dialogs
- __Lightbox__: `bg-black/95 backdrop-blur fixed inset-0 z-50` - Full-screen photo viewer

### Typography

- __Font__: System font stack (SF Pro, Segoe UI, Roboto)
- __Headings__: `text-xl font-semibold text-gray-100`
- __Body__: `text-sm text-gray-400`
- __Monospace__: `font-mono text-xs` - File paths, technical info

## Data Model

### Database Schema (SQLite)

```sql
-- Photos table
CREATE TABLE photos (
    id TEXT PRIMARY KEY,              -- SHA256 hash
    file_path TEXT NOT NULL,          -- Relative path from mounted dir
    filename TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP,             -- From EXIF or file
    modified_at TIMESTAMP,
    indexed_at TIMESTAMP,
    thumbnail_path TEXT,
    original_path TEXT                -- Set when photo is in recycle bin
);

-- Albums table
CREATE TABLE albums (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP
);

-- Tags table
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Photo-Album junction (many-to-many)
CREATE TABLE photo_albums (
    photo_id TEXT,
    album_id TEXT,
    added_at TIMESTAMP,
    PRIMARY KEY (photo_id, album_id),
    FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
    FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
);

-- Photo-Tag junction (many-to-many)
CREATE TABLE photo_tags (
    photo_id TEXT,
    tag_id TEXT,
    added_at TIMESTAMP,
    PRIMARY KEY (photo_id, tag_id),
    FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Metadata table (EXIF data)
CREATE TABLE metadata (
    photo_id TEXT PRIMARY KEY,
    camera_make TEXT,                 -- Camera manufacturer (e.g., Canon, Nikon)
    camera_model TEXT,                -- Camera model (e.g., EOS 5D Mark IV)
    lens_model TEXT,                  -- Lens model
    focal_length TEXT,                -- Focal length (e.g., 50mm)
    aperture TEXT,                    -- F-stop (e.g., f/2.8)
    shutter_speed TEXT,               -- Shutter speed (e.g., 1/500)
    iso INTEGER,                      -- ISO value
    date_taken TIMESTAMP,             -- Original date/time photo was taken
    gps_latitude REAL,                -- GPS latitude
    gps_longitude REAL,               -- GPS longitude
    FOREIGN KEY (photo_id) REFERENCES photos(id) ON DELETE CASCADE
);

-- Action log for rollback system
CREATE TABLE action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,        -- photo_create, photo_update, photo_delete, photo_restore, etc.
    photo_id TEXT,
    old_value TEXT,                   -- JSON of previous state
    new_value TEXT,                   -- JSON of new state
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_rolled_back INTEGER DEFAULT 0
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_photos_path ON photos(file_path);
CREATE INDEX idx_photos_filename ON photos(filename);
CREATE INDEX idx_photos_created ON photos(created_at);
CREATE INDEX idx_photo_albums_album ON photo_albums(album_id);
CREATE INDEX idx_photo_tags_tag ON photo_tags(tag_id);
CREATE INDEX idx_action_log_timestamp ON action_log(timestamp);
CREATE INDEX idx_action_log_photo ON action_log(photo_id);
```

## Project Structure

```
photo-manager/
  backend/
    main.py                    # FastAPI app entry point
    config.py                  # Environment config
    database.py                # SQLite connection & schema
    models/
      photo.py                 # Photo model
      album.py                 # Album model
      tag.py                   # Tag model
    api/
      photos.py                # Photo endpoints
      albums.py                # Album endpoints
      tags.py                  # Tag endpoints
      search.py                # Search endpoints
    services/
      scanner.py               # Photo library scanner
      watcher.py               # Filesystem watcher (watchdog)
      thumbnail.py             # Thumbnail generator
      exif.py                  # EXIF extractor
      file_ops.py              # Move/rename/delete
      recycle_bin.py           # Recycle bin operations
      action_logger.py         # Action logging and rollback
    utils/
      hashing.py               # SHA256 hashing
      validators.py            # Path validation
  frontend/
    static/
      css/
        tailwind.min.css       # Downloaded from CDN
      js/
        alpine.min.js          # Downloaded from CDN
        app.js                 # Main app logic
      icons/
        feather-sprite.svg
    templates/
      index.html               # Main SPA
  data/                        # Docker volume (persistent)
    metadata/
      photos.db                # SQLite database
    cache/
      thumbnails/              # Generated thumbnails
    recycle-bin/               # Soft-deleted photos
  photos/                      # Docker volume (mounted host dir)
  .env.example
  .gitignore
  Dockerfile
  docker-compose.yml
  requirements.txt
  README.md
```

## API Endpoints

### Photos

- `GET /api/photos` - List photos (paginated, with filters)
- `GET /api/photos/{id}` - Get photo details (includes EXIF data from metadata table)
- `GET /api/photos/{id}/thumbnail` - Get thumbnail image file (200px, optimized for gallery grid)
- `GET /api/photos/{id}/preview` - Get medium-size preview image (1200px, optimized for lightbox)
- `GET /api/photos/{id}/image` - Get full-size original image file (for download)
- `GET /api/photos/duplicates` - Scan filesystem for duplicate photos (by hash)
- `PUT /api/photos/{id}/move` - Move photo to new folder path
- `PUT /api/photos/{id}/rename` - Rename photo
- `DELETE /api/photos/{id}` - Delete photo (soft delete to recycle bin)

### Albums

- `GET /api/albums` - List all albums
- `GET /api/albums/{id}` - Get album with photos
- `POST /api/albums` - Create album
- `PUT /api/albums/{id}` - Update album
- `DELETE /api/albums/{id}` - Delete album
- `POST /api/albums/{id}/photos` - Add photos to album
- `DELETE /api/albums/{id}/photos/{photo_id}` - Remove photo from album

### Tags

- `GET /api/tags` - List all tags
- `POST /api/tags` - Create tag
- `PUT /api/tags/{id}` - Update tag name
- `DELETE /api/tags/{id}` - Delete tag
- `POST /api/tags/{id}/photos` - Tag photos
- `DELETE /api/tags/{id}/photos/{photo_id}` - Untag photo

### Search

- `GET /api/search?q={query}&tags={}&albums={}&from={date}&to={date}` - Search photos by filename

### Folders

- `GET /api/folders` - Get hierarchical folder tree structure (JSON)
- `GET /api/folders/{path}` - List photos in specific folder
- `POST /api/folders` - Create new folder

### Recycle Bin

- `GET /api/recycle-bin` - List deleted photos in recycle bin
- `POST /api/recycle-bin/{id}/restore` - Restore photo from recycle bin
- `DELETE /api/recycle-bin/{id}` - Permanently delete photo from recycle bin
- `DELETE /api/recycle-bin/empty` - Empty entire recycle bin

### Action Log & Rollback

- `GET /api/action-log` - Get recent action history
- `POST /api/action-log/rollback` - Rollback to a specific point in time

### System

- `POST /api/scan` - Trigger library scan
- `GET /api/stats` - Library statistics

## Dependencies

### requirements.txt

```txt
fastapi==0.119.1
uvicorn[standard]==0.38.0
Pillow==12.0.0
watchdog==6.0.0
rawpy==0.25.1
```

### Frontend (no package.json)

- Download once and commit to repo:

```bash
# Alpine.js
curl -o frontend/static/js/alpine.min.js https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js

# Tailwind CSS (use CDN in development, can generate custom build later)
# In HTML: <script src="https://cdn.tailwindcss.com"></script>

# Feather Icons sprite
curl -o frontend/static/icons/feather-sprite.svg https://unpkg.com/feather-icons/dist/feather-sprite.svg
```

__Note__: Tailwind via CDN is fine for MVP. For production, can generate a custom build with only dark theme classes.

## Dockerfile

```dockerfile
FROM python:3.13-slim

# Install system dependencies for RAW photo support
RUN apt-get update && apt-get install -y \
    libraw-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ ./backend/
COPY frontend/ ./frontend/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## docker-compose.yml

```yaml
version: '3.8'

services:
  photo-manager:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./photos:/photos:rw           # Host photos directory
      - photo-data:/app/data          # Persistent metadata & cache
    environment:
      - PHOTOS_PATH=/photos
      - DATABASE_PATH=/app/data/metadata/photos.db
      - THUMBNAIL_PATH=/app/data/cache/thumbnails
      - RECYCLE_BIN_PATH=/photos/.recycle-bin
      - ACTION_LOG_MAX_RECORDS=1000
      - SCAN_ON_STARTUP=true
      - AUTO_WATCH=true
    restart: unless-stopped

volumes:
  photo-data:
```

## MVP Development Plan

### 🎯 Core Features

__Goal__: Working photo browser with file management
__Deliverables__:

- [ ] Docker setup with FastAPI + SQLite
- [ ] Database schema and migrations (including recycle bin table)
- [ ] Photo scanner (index existing photos by SHA256, skip duplicates)
- [ ] Duplicate detection and review UI
- [ ] Filesystem watcher (auto-detect new photos with watchdog)
- [ ] Thumbnail generator (JPEG/PNG/GIF/WebP/RAW, 300px)
- [ ] RAW photo support (view embedded preview or render to JPEG)
- [ ] EXIF extraction (camera make/model, lens, aperture, shutter, ISO, date, GPS)
- [ ] API: Get hierarchical folder tree with recursive photo counts
- [ ] API: List photos in specific folder (paginated, sorted by name)
- [ ] API: Get photo details with EXIF data
- [ ] API: Create folders with path validation
- [ ] API: Move files (update file_path in database)
- [ ] API: Rename files (update filename and file_path in database)
- [ ] API: Delete files (soft delete to recycle bin)
- [ ] API: CRUD albums and tags (including PUT for tag updates)
- [ ] API: Add/remove photos to/from albums/tags
- [ ] API: Simple search (filename only, with tag/album/date filters)
- [ ] API: Recycle bin (list, restore, permanent delete, empty)
- [ ] Frontend: Dark theme layout (Tailwind gray-900/800 palette)
- [ ] Frontend: Persistent folder tree sidebar (always visible, collapsible folders)
- [ ] Frontend: Gallery grid (Alpine.js + Tailwind, sorted by filename)
- [ ] Frontend: Folder navigation and selection in tree
- [ ] Frontend: Create folder button in sidebar
- [ ] Frontend: Lightbox viewer with keyboard shortcuts
- [ ] Frontend: Album/tag management UI
- [ ] Frontend: File operations (move/rename/delete buttons)
- [ ] Frontend: Recycle bin UI in sidebar with restore/delete
- [ ] Frontend: Duplicates section in sidebar
- [ ] Frontend: Search interface with filters
- [ ] Frontend: Icon set (Feather icons)
- [ ] Frontend: Drag-and-drop photos to folders, albums, and tags
- [ ] Frontend: Quick add to album modal with batch operations
- [ ] Frontend: Quick add tag modal with batch operations
- [ ] Frontend: Breadcrumb navigation for folder hierarchy
- [ ] Frontend: Browse up button to navigate to parent folder
- [ ] Frontend: Folder icons in gallery showing subfolders
- [ ] Frontend: Hover action buttons (album, tag, restore)
- [ ] Frontend: High-quality preview images in lightbox (1200px)
- [ ] Frontend: Download button for full-size images
- [ ] Frontend: 8-column gallery grid for higher density
- [ ] FastAPI serves static files
- [ ] Pagination (page/limit format, 50 photos default)
- [ ] Error notifications (Alpine.js toast)
- [ ] Database indexes for performance

## Key Implementation Notes

### Photo Identification

- Use SHA256 hash of file content as primary key
- Allows photos to be moved without breaking metadata links
- Detects duplicates automatically
- Handle hash collisions gracefully (unlikely but possible)

### Duplicate Photo Handling

- Photos are identified by SHA256 hash (content-based)
- **During scanning**: When hash already exists in database, skip indexing (don't create new record)
- **Duplicate detection approach**: On-demand filesystem scan
  - When user opens "Duplicates" view, scan filesystem for files with same hash
  - Compare filesystem files against database records to find unindexed duplicates
  - Display both indexed photo and duplicate file paths
- **Duplicate Review UI**: Show list of duplicate photos with:
  - Primary photo (indexed in database) with its path
  - List of duplicate file paths found on filesystem
  - Ability to delete duplicate files (physical deletion, not in database)
  - Keep one canonical copy in database
- **API**: `GET /api/photos/duplicates` - Scans filesystem and returns duplicate groups
- **Frontend**: "Duplicates" section in sidebar showing count of duplicate groups
- **Note**: Duplicates not stored in database; found via on-demand filesystem comparison
- **Performance**: Duplicate scan may be slow with 20k+ photos (hashes entire filesystem); consider caching results

### Thumbnail & Preview Generation

#### Thumbnails (Gallery Grid)
- Generate on-demand, cache to disk
- Size: 200px (longest side), JPEG quality 80
- Path: `/data/cache/thumbnails/{photo_id}.jpg`
- Optimized for fast loading in gallery grid view
- Since photo ID is SHA256 hash of content, thumbnails never need regeneration
- If file content changes, it gets a new hash/ID and new thumbnail
- __RAW files__: Use rawpy to extract embedded JPEG preview or render to RGB
- RAW thumbnail generation may take 1-3 seconds (acceptable for MVP)

#### Preview Images (Lightbox)
- Generate on-demand, cache to disk
- Size: 1200px (longest side), JPEG quality 90
- Path: `/data/cache/thumbnails/{photo_id}_preview.jpg`
- Optimized for high-quality viewing in lightbox modal
- Provides better viewing experience than thumbnails
- Balances quality and file size for web viewing
- __RAW files__: Full postprocess rendering for best quality
- Cached separately from thumbnails for optimal performance

### RAW Photo Handling

- Use `rawpy` library to read RAW formats (CR2, NEF, ARF, DNG, ORF, RW2, etc.)
- For thumbnails: Extract embedded JPEG preview if available (fast)
- For full view: Render RAW to RGB array, convert to JPEG (slower but better quality)
- Store rendered JPEG in cache alongside thumbnails
- Supported formats: Canon (CR2, CR3), Nikon (NEF), Sony (ARF), Adobe (DNG), and more
- View-only (no RAW editing capabilities)

### Filesystem Watcher

- Use watchdog library to monitor `/photos` directory
- Automatically index new photos when added to filesystem
- Detect file modifications and deletions
- **External deletions**: When file deleted outside app, hard delete database record (no recycle bin)
- **External modifications**: If file content changes, treat as new photo with new hash
- Run in background thread on application startup
- Can be disabled via `AUTO_WATCH=false` environment variable
- Debounce rapid file additions (wait 1 second after last event)
- Handle Docker volume mount limitations gracefully

### Folder Tree API Response

The `/api/folders` endpoint returns a hierarchical JSON structure with:

- Folder name and path
- **Photo count for each folder**: Recursive count (includes all photos in subfolders)
- Recursive children array for nested folders
- Support for nesting to any depth
- Empty children array for leaf folders
- Frontend recursively renders tree using Alpine.js

### Recycle Bin Implementation

- **Soft delete**: `DELETE /api/photos/{id}` moves photo to recycle bin (not permanent)
- **Physical file**: Move file to `/photos/.recycle-bin/{photo_id}/{filename}` on filesystem
- **Database**: Update photo record with:
  - `original_path`: Set to original file path before deletion
  - `file_path`: Update to `.recycle-bin/{photo_id}/{filename}`
  - All metadata, album, and tag relationships remain intact in database
- **Restore with Conflict Resolution**:
  - Check if file exists at both original location and recycle bin
  - If file already at original location: Skip file move, just restore database records
  - If file only in recycle bin: Move file back to original location
  - If file in neither location: Error (cannot restore)
  - Update photo record: restore `file_path` to `original_path`, clear `original_path`
  - All metadata, album, and tag relationships automatically restored (never deleted)
- **Frontend Restore UI**:
  - Restore button visible on hover in recycle bin view
  - Yellow accent color for restore button (distinct from delete/move)
  - Confirmation dialog before restoring
  - Error messages display conflict details
  - Success notification after restore
- **Permanent delete**: Remove file from filesystem and recycle bin table
- **Empty recycle bin**: Delete all files and records in recycle bin
- **Auto-cleanup**: Optional feature to auto-delete items older than 30 days (not in MVP)
- Recycle bin visible in sidebar with count of deleted items

### Rollback System Implementation

- **Automatic action logging**: All user operations logged via SQLite triggers
- **13 SQLite triggers** capture changes automatically:
  - `log_photo_create`: When new photo indexed
  - `log_photo_update`: When photo moved/renamed
  - `log_photo_delete`: When photo moved to recycle bin
  - `log_photo_restore`: When photo restored from recycle bin
  - `log_album_create/update/delete`: Album operations
  - `log_tag_create/update/delete`: Tag operations
  - `log_photo_album_add/remove`: Photo-album associations
  - `log_photo_tag_add/remove`: Photo-tag associations
- **Action log table**: Stores all operations with:
  - `action_type`: Type of operation performed
  - `photo_id`: Affected photo (if applicable)
  - `old_value`: JSON snapshot of previous state
  - `new_value`: JSON snapshot of new state
  - `timestamp`: When action occurred
  - `is_rolled_back`: Flag indicating if action was rolled back
- **Point-in-time rollback**: Execute inverse operations in reverse chronological order
  - User selects point in history to rollback to
  - System executes inverse of each action from that point forward
  - Example: photo_delete → restore photo, photo_album_add → remove from album
- **Rollback operations**:
  - `photo_create` → Delete photo
  - `photo_delete` → Restore photo from recycle bin
  - `photo_update` → Restore previous file_path and filename
  - `album_create` → Delete album
  - `tag_create` → Delete tag
  - `photo_album_add` → Remove photo from album
  - `photo_tag_add` → Remove tag from photo
  - And inverse operations for removals/deletions
- **Retention policy**: Keep last 1000 actions (configurable via ACTION_LOG_MAX_RECORDS)
- **Automatic cleanup**: Triggers remove old entries beyond retention limit
- **Frontend UI**:
  - Action log viewer showing recent operations
  - Rollback button for each action
  - Visual indication of rolled-back actions (grayed out)
  - Confirmation dialog before rollback
- **Exclusions**: Scanner operations don't create action log entries (prevents log pollution)

### Move/Rename Operations

- **Move photo**: `PUT /api/photos/{id}/move`
  - Move physical file on filesystem
  - Update `file_path` field in database
  - Photo ID (hash) remains unchanged
  - Maintains all metadata, album, and tag relationships
- **Rename photo**: `PUT /api/photos/{id}/rename`
  - Rename physical file on filesystem
  - Update `filename` and `file_path` fields in database
  - Photo ID (hash) remains unchanged

### Drag-and-Drop Interface

#### Photo Dragging
- **Drag source**: Any photo in gallery grid
- **Draggable attribute**: `draggable="true"` on photo cards
- **Drag start**: Store photo ID in dataTransfer, add visual feedback
- **Custom drag image**: 80px rounded preview with blue border
- **Dragging class**: Reduce opacity and scale of original element during drag
- **Drag end**: Remove visual feedback classes

#### Drop Targets
- **Folders in sidebar tree**: Drop to move photo to folder
  - Blue highlight on dragover
  - Remove highlight on dragleave
  - Call `/api/photos/{id}/move` on drop
  - Refresh current view and folder tree after move
- **Folders in gallery grid**: Drop to move photo to subfolder
  - Same behavior as sidebar folders
- **Albums in sidebar**: Drop to add photo to album
  - Blue highlight on dragover
  - Call `/api/albums/{id}/photos` POST endpoint on drop
  - Reload album counts after addition
- **Tags in sidebar**: Drop to add tag to photo
  - Green highlight on dragover (distinct from albums)
  - Call `/api/tags/{id}/photos` POST endpoint on drop
  - Reload tag counts after addition

#### Visual Feedback
- **Drag ghost**: Semi-transparent 80px thumbnail follows cursor
- **Drop zone highlight**: Blue for folders/albums, green for tags
- **Opacity animation**: Smooth transition on drag start/end
- **Scale animation**: Slight shrink during drag (0.8 scale)
- **Cursor**: Shows move/copy cursor depending on target

### Quick Album/Tag Management

#### Add to Album Modal
- **Trigger**: Click album icon button on photo hover
- **UI**: Modal with checklist of all albums
- **State management**: Track pending add/remove changes
- **Checkbox behavior**:
  - Checked = photo is in album
  - Toggle checkbox to mark for add/remove
  - Changes not applied until "Done" clicked
- **Batch changes**: Apply all additions first, then all removals
- **API calls**:
  - POST `/api/albums/{id}/photos` for additions
  - DELETE `/api/albums/{id}/photos/{photo_id}` for removals
- **After save**: Refresh current view and reload album counts
- **Cancel**: Discard all pending changes

#### Add Tag Modal
- **Trigger**: Click tag icon button on photo hover
- **UI**: Modal with checklist of all tags
- **State management**: Track pending add/remove changes
- **Checkbox behavior**:
  - Checked = photo has tag
  - Toggle checkbox to mark for add/remove
  - Changes not applied until "Done" clicked
- **Batch changes**: Apply all additions first, then all removals
- **API calls**:
  - POST `/api/tags/{id}/photos` for additions
  - DELETE `/api/tags/{id}/photos/{photo_id}` for removals
- **After save**: Refresh current view and reload tag counts
- **Green color scheme**: Distinct from albums (blue)
- **Cancel**: Discard all pending changes

#### Hover Actions
- **Action buttons**: Show album/tag buttons on photo hover
- **Icon design**: Small rounded buttons with icons
- **Position**: Top-right corner of photo card
- **Opacity transition**: Fade in on hover, fade out on hover exit
- **Z-index**: Above photo but below modals
- **Colors**: Blue for album, green for tag, yellow for restore

### Enhanced Folder Navigation

#### Folder Display in Gallery
- **Visual distinction**: Blue border (not gray like photos)
- **Folder icon**: Large SVG folder icon in center
- **Photo count**: Display count below folder name
- **Hover effect**: Lighter blue border on hover
- **Click behavior**: Navigate into folder (same as sidebar)
- **Double-click**: Expand folder in sidebar tree
- **Drag target**: Can drop photos to move into folder

#### Folder Query Logic (Non-Recursive)
- **Root folder (`path=""`)**: Match files with NO "/" in path
  - SQL: `WHERE file_path NOT LIKE '%/%'`
  - Example: "photo.jpg" matches, "folder/photo.jpg" doesn't
- **Specific folder (`path="Wallpaper"`)**: Match files with exactly one more "/" than folder path
  - SQL: `WHERE file_path LIKE 'Wallpaper/%' AND (LENGTH(file_path) - LENGTH(REPLACE(file_path, '/', ''))) = 1`
  - Example: "Wallpaper/photo.jpg" matches, "Wallpaper/Cats/photo.jpg" doesn't
- **Purpose**: Show only direct children, not all descendants
- **Performance**: Efficient SQL query using string length comparison

#### Breadcrumb Navigation
- **Location**: Header bar above gallery grid
- **Root**: Always shows "Photos" as clickable root
- **Path parts**: Each folder in path is clickable link
- **Separators**: "/" between path segments
- **Current folder**: Last item is highlighted (not a link)
- **Click behavior**: Jump directly to any parent folder
- **Color scheme**: Blue links for navigation, gray text for current

#### Browse Up Button
- **Visibility**: Only show when not at root folder
- **Icon**: Folder with left arrow
- **Position**: Left of breadcrumbs
- **Behavior**: Navigate to parent folder
- **Keyboard**: Could add "Backspace" shortcut in future

#### Folder Tree Enhancements
- **Hide root**: Don't render "Photos" root node, show children directly
- **Collapsed by default**: Folders start collapsed for cleaner UI
- **Expandable indicator**: Triangle (▶) when collapsed, (▼) when expanded
- **Active state**: Blue highlight for currently viewed folder
- **Drag targets**: All folders accept dropped photos

### Path Validation (Security)

- All file operations must validate path is within mounted directory
- Prevent path traversal attacks (../, absolute paths)
- Normalize paths before validation
- Reject symlinks outside mounted directory
- Folder creation must validate parent directory exists
- Prevent duplicate folder names (return error if folder exists)

### Pagination

- **API format**: `GET /api/photos?page=1&limit=50`
- Default page size: 50 photos per page
- Response includes: total count, current page, total pages, photos array
- All photo list endpoints support pagination (folder views, album views, search results)

### Search Implementation

- **Simple search**: `GET /api/search?q={query}`
- Search scope: Filename only (case-insensitive partial match)
- Filter by tags: `&tags=tag1,tag2` (comma-separated, AND logic)
- Filter by albums: `&albums=album1,album2` (comma-separated, OR logic)
- Filter by date range: `&from=2024-01-01&to=2024-12-31`
- All filters combine with AND logic
- Returns paginated results, sorted by filename (ascending)

### Photo Sort Order

- **Default sort**: Filename (ascending, case-insensitive)
- Gallery grid displays photos in filename order
- Lightbox navigation follows same sort order
- Optional future enhancement: User-configurable sort (date, size, name)

### Frontend State Management (Alpine.js)

- Use Alpine.js reactive data binding with x-data
- Main app state:
  - `folderTree`: Hierarchical folder structure
  - `expandedFolders`: Set of folder paths that are expanded
  - `currentFolder`: Currently selected folder path
  - `currentView`: Current view type ('folder', 'album', 'tag', 'all', 'search', 'recycle-bin')
  - `currentViewLabel`: Display label for current view
  - `photos`: Array of photos in current view
  - `folders`: Array of subfolders in current directory
  - `albums`: Array of all albums
  - `tags`: Array of all tags
  - `selectedPhoto`: Photo in lightbox
  - `lightboxOpen`: Boolean for lightbox visibility
  - `actionLog`: Array of recent actions for rollback
  - `selectedPhotoForAlbum`: Photo being added to albums
  - `selectedPhotoForTag`: Photo being tagged
  - `photoAlbums`: Array of album IDs the current photo belongs to
  - `photoTags`: Array of tag IDs the current photo has
  - `pendingAlbumChanges`: Object tracking add/remove changes
  - `pendingTagChanges`: Object tracking add/remove changes
  - `showCreateFolder`: Boolean for folder creation modal
  - `showAddToAlbum`: Boolean for album modal
  - `showAddTag`: Boolean for tag modal
  - `newFolderPath`: Input value for new folder name
  - `newFolderParent`: Parent path for new folder
- Use x-for for rendering folder tree, photo grids, and folder grids
- Use x-show/x-if for conditional rendering (expanded folders, modals, buttons)
- Use @click for event handling (folder expand/collapse, selection)
- Use @dragstart, @dragend, @dragover, @dragleave, @drop for drag-and-drop
- Use @click.stop for preventing event propagation (expand arrows, action buttons)
- Fetch API for HTTP requests to backend
- Recursive component pattern for nested folder tree

### Dark Theme Implementation

- Set `<html class="dark">` or `<body class="bg-gray-900 text-gray-100">`
- Use Tailwind's dark color palette (gray-900, gray-800, gray-700)
- All components styled with dark theme colors by default
- Photo thumbnails: border-gray-700 for subtle framing
- Hover states: brightness-110 for photo cards
- Lightbox: black/95 with backdrop-blur for photo focus
- Modals: gray-800 with gray-700 borders
- No light theme toggle (dark only for simplicity)

### Keyboard Shortcuts

- Arrow keys: Navigate between photos in lightbox
- Escape: Close lightbox or modal
- Delete: Delete current photo (with confirmation)
- Up/Down: Navigate folder tree (optional enhancement)
- Enter: Expand/collapse folder or open selected photo

## Testing Strategy

- Manual testing of basic flows
- Test with 1000 sample photos (mix of JPEG, PNG, RAW, including duplicates)
- Test duplicate detection and review UI
- Test folder tree navigation (expand/collapse, selection, deep nesting)
- Test folder tree recursive photo counts
- Test folder tree performance with 100+ folders
- Test folder tree hiding root node (shows children directly)
- Test RAW photo viewing (CR2, NEF, DNG formats)
- Test filesystem watcher (add/modify/delete photos externally)
- Test folder creation from sidebar (valid paths, duplicates, invalid paths)
- Test file operations (move updates file_path, rename updates both fields)
- Test drag-and-drop photos to folders (sidebar and gallery)
- Test drag-and-drop photos to albums
- Test drag-and-drop photos to tags
- Test drag ghost visual feedback and opacity changes
- Test quick add to album modal (batch add/remove)
- Test quick add tag modal (batch add/remove)
- Test hover action buttons (album, tag, restore)
- Test recycle bin (delete, restore with conflict resolution, permanent delete, empty)
- Test restore when file already at destination
- Test restore when file only in recycle bin
- Test breadcrumb navigation (click to jump to parent folders)
- Test browse up button navigation
- Test folder icons in gallery with photo counts
- Test non-recursive folder queries (only direct children)
- Test rollback system (undo photo delete, move, album/tag changes)
- Test action log retention (keeps last 1000 actions)
- Test rollback UI (action log viewer, rollback buttons)
- Test lightbox with preview images (1200px, quality 90)
- Test download full-size images from lightbox
- Test EXIF data extraction and display
- Test album and tag management (including tag rename)
- Test search functionality (filename search with filters)
- Test pagination (page/limit parameters)
- Test photo sort order (alphabetical by filename)
- Test 8-column gallery grid layout

## Success Criteria

- ✅ Browse 10k photos without crashes
- ✅ Duplicate photos detected and flagged for review
- ✅ Folder tree always visible and responsive (expand/collapse)
- ✅ Folder tree shows recursive photo counts accurately
- ✅ Folder tree handles 100+ folders smoothly
- ✅ Folder tree hides root node for cleaner interface
- ✅ Dark theme looks polished and minimal
- ✅ RAW photos display correctly (CR2, NEF, DNG)
- ✅ EXIF data extracted and displayed correctly
- ✅ New photos detected within 2 seconds of being added
- ✅ Move/rename operations update database file_path correctly
- ✅ Drag-and-drop photos to folders, albums, and tags works smoothly
- ✅ Quick add to album/tag modals support batch operations
- ✅ Hover action buttons appear on photo hover
- ✅ Breadcrumb navigation allows jumping to any parent folder
- ✅ Browse up button navigates to parent folder
- ✅ Folder icons in gallery show subfolders with counts
- ✅ Non-recursive folder queries return only direct children
- ✅ Delete moves photos to recycle bin (not permanent)
- ✅ Restore from recycle bin works with conflict resolution
- ✅ Restore handles case when file already at destination
- ✅ Rollback system logs all user operations automatically
- ✅ Rollback to any point in action history works correctly
- ✅ Action log retains last 1000 actions
- ✅ Thumbnails load <2s per page (JPEG/PNG, 200px)
- ✅ Preview images in lightbox are high quality (1200px, 90% quality)
- ✅ Download button provides full-size original images
- ✅ RAW thumbnails generate within 5 seconds
- ✅ RAW previews generate within 10 seconds (higher quality)
- ✅ Search by filename returns results in <1 second
- ✅ Photos sorted alphabetically by filename
- ✅ Pagination works correctly (page/limit)
- ✅ Data persists after container restart
- ✅ 8-column gallery grid displays more photos per view
- ✅ Gallery grid responsive and smooth with drag-and-drop

## Quick Start Commands

```bash
# Setup
git clone <repo>
cd photo-manager
cp .env.example .env
# Edit .env: Set PHOTOS_PATH to your photo directory

# Run
docker-compose up -d

# Access
open http://localhost:8000

# Logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

## Environment Variables (.env)

```bash
# Paths
PHOTOS_PATH=/path/to/your/photos
DATABASE_PATH=/app/data/metadata/photos.db
THUMBNAIL_PATH=/app/data/cache/thumbnails
RECYCLE_BIN_PATH=/app/data/recycle-bin

# Performance
THUMBNAIL_SIZE=200
THUMBNAIL_QUALITY=80
SCAN_ON_STARTUP=true
AUTO_WATCH=true

# Action log
ACTION_LOG_MAX_RECORDS=1000
```

## Development Workflow

1. __Edit code__ (backend/*.py or frontend/*.html/js)
2. __Refresh browser__ (frontend changes are instant)
3. __Restart container__ (only for backend changes): `docker-compose restart`
4. __Check logs__ for errors: `docker-compose logs -f`

No build step. No npm install. No webpack. Just code and run.

## Common Tasks

### Add a new API endpoint

1. Add route in `backend/api/{resource}.py`
2. Update model in `backend/models/{resource}.py` if needed
3. Test with browser or curl
4. Update frontend to call new endpoint

### Add a new frontend component

1. Create function in `frontend/static/js/app.js` or new file
2. Use Alpine.js directives in `frontend/templates/index.html`
3. Style with Tailwind dark theme classes (bg-gray-900, text-gray-100, etc.)
4. Refresh browser to see changes

### Run database migration

1. Add migration script in `backend/database.py`
2. Execute migration on container startup or via manual script
3. Update schema version tracking

## Known Limitations

- External changes: Auto-detected via watchdog (may have delays with Docker volumes)
- External deletions: Hard delete from database (no recycle bin for external deletions)
- Duplicate handling: Scanner skips duplicates; review UI is manual (no auto-merge)
- Scale: Optimized for 20k photos (not tested beyond 50k)
- Single user only
- No upload functionality (manage existing photos only)
- Search: Filename only (no EXIF or full-text search)
- Sort: Fixed alphabetical by filename (no user-configurable sort)
- EXIF data: Common fields only (camera, lens, settings, GPS)
- RAW photos: View-only (no editing, renders to JPEG for display)
- RAW thumbnail generation slower than JPEG (1-3 seconds vs <500ms)
- RAW preview generation for lightbox (5-10 seconds first time)
- Recycle bin: No auto-cleanup (manual empty required)
- Drag-and-drop: Single photo at a time (no multi-select drag)
- Album/tag modals: Must check albums individually (no "add to all" bulk action)
- Rollback: Cannot rollback scanner operations (only user actions)
- Action log: Limited to last 1000 actions (configurable, older actions purged)

## Recent Enhancements (Since Initial MVP)

### UX & Navigation Improvements
- **Drag-and-drop interface**: Drag photos to folders, albums, and tags
- **Quick album/tag management**: Modal dialogs for batch add/remove operations
- **Breadcrumb navigation**: Click any parent folder to jump directly
- **Browse up button**: Navigate to parent folder with single click
- **Folder icons in gallery**: Subfolders displayed alongside photos with counts
- **Hover action buttons**: Quick access to album/tag/restore actions
- **8-column gallery grid**: Higher density layout (was 5 columns)

### Folder Navigation
- **Non-recursive folder queries**: Show only direct children (performance)
- **Hide root node**: Cleaner folder tree (show children directly)
- **Collapsed by default**: Folders start collapsed for cleaner UI
- **Better SQL queries**: Efficient path matching using string length comparison

### Image Quality
- **Preview images for lightbox**: 1200px high-quality previews (was using thumbnails)
- **Separate thumbnail/preview caching**: Optimized for gallery vs. lightbox
- **Download full-size images**: New download button in lightbox
- **Smaller thumbnails**: 200px instead of 300px for faster grid loading

### Recycle Bin
- **Simplified architecture**: Single `original_path` column instead of separate table
- **Conflict resolution on restore**: Handle case when file already at destination
- **Smart restore logic**: Update photo record instead of complex JSON serialization
- **Visual restore button**: Yellow button with restore icon on hover
- **Better error messages**: Clear feedback on restore conflicts
- **Recycle bin in photos folder**: `.recycle-bin/` subdirectory for better organization

### Rollback System
- **Automatic action logging**: 13 SQLite triggers capture all user operations
- **Point-in-time recovery**: Rollback to any action in history
- **Inverse operations**: System automatically executes inverse of each action
- **Simple retention**: Keep last 1000 actions (configurable)
- **Frontend UI**: Action log viewer with rollback buttons
- **Visual feedback**: Grayed-out rolled-back actions
- **No scan pollution**: Scanner operations excluded from action log

### Dependencies
- **Updated to latest packages**: FastAPI 0.119.1, Pillow 12.0.0, uvicorn 0.38.0, watchdog 6.0.0

## Future Enhancements (Not in Scope)

- Multi-user support with authentication
- Upload functionality
- Video support
- Multi-select and batch operations (delete/move multiple photos)
- RAW editing (currently view-only)
- Mobile responsive design
- Light theme toggle (dark theme only for MVP)
- Advanced duplicate detection (perceptual hashing, auto-merge)
- Map view for GPS-tagged photos
- User-configurable sort options (date, size, custom)
- Full-text search (EXIF metadata, captions)
- Auto-cleanup recycle bin (age-based deletion)
- Cloud storage integration
- Facial recognition and auto-tagging
- Keyboard shortcuts for drag-and-drop
- Multi-photo drag (drag selection of photos)
