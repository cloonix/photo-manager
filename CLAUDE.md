# Photo Manager - Development Notes

## Project Summary

A lightweight, self-contained photo management application built following the specifications in `SPECIFICATIONS.md`. This is a single-user photo manager designed to handle 10k-50k photos with minimal dependencies and maximum simplicity.

## What Was Built

### Backend (Python 3.13 + FastAPI)
- **Database**: SQLite with complete schema (photos, albums, tags, metadata)
- **Services**:
  - Photo scanner with SHA256 content hashing
  - Filesystem watcher for auto-detection of new photos
  - EXIF metadata extraction
  - Thumbnail generation (including RAW support via rawpy)
  - File operations (move, rename, delete)
  - Recycle bin with restore functionality
- **API Endpoints**: Full REST API with 6 routers (photos, folders, albums, tags, search, recycle-bin)
- **Configuration**: Environment-based config with sensible defaults

### Frontend (Alpine.js + Tailwind CSS)
- **Single Page Application**: Zero build tools, vanilla JS approach
- **Dark Theme**: Minimalist gray-900/800 color palette
- **Features**:
  - Persistent folder tree sidebar (always visible, collapsible)
  - Album and tag management with inline creation
  - Search functionality
  - Lightbox viewer with keyboard navigation and top-center controls
  - Recycle bin UI with restore functionality
  - Multi-photo selection (Google Photos style)
  - Drag & drop (photos to folders/albums/tags/recycle bin)
  - Toast notifications (no browser alerts)
  - Custom confirmation modals
  - Pagination support

### Docker Setup
- **Dockerfile**: Python 3.13-slim with libraw for RAW support
- **docker-compose.yml**: Configured with persistent volumes for data and photos
- **Volumes**:
  - `./photos:/photos:rw` - Mount your photos here
  - `photo-data:/app/data` - Persistent metadata, cache, and recycle bin

## Key Implementation Details

### Content-Addressable Storage
- Photos identified by SHA256 hash of file content
- Enables deduplication and survives file moves
- Thumbnails cached by hash (never need regeneration)

### Folder Tree
- Recursive folder structure with photo counts
- Expandable/collapsible folders in sidebar
- Non-recursive photo loading per folder

### Recycle Bin
- Soft-delete using `deleted_at` timestamp column
- Physical files remain in place (not moved)
- All metadata, albums, and tags preserved
- Restore clears `deleted_at` timestamp
- "Empty Recycle Bin" button permanently deletes files and DB records

### RAW Photo Support
- Extracts embedded JPEG preview when available (fast)
- Falls back to rendering RAW to RGB (slower but universal)
- Supported: CR2, CR3, NEF, ARF, DNG, ORF, RW2, ARW

## Tech Stack
- **Backend**: FastAPI 0.104.1, uvicorn, Pillow 10.1.0, watchdog 3.0.0, rawpy 0.19.0
- **Frontend**: Alpine.js 3.x (CDN), Tailwind CSS (CDN), Feather Icons
- **Database**: SQLite with proper indexes
- **Container**: Python 3.13-slim base image

## Recent Improvements (Nov 2025)

### Major Refactoring
- **Consolidated authentication** - Single `auth()` function in `backend/dependencies.py` (~108 lines eliminated)
- **Simplified recycle bin** - Soft-delete with `deleted_at` timestamp instead of file moves (~240 lines eliminated)
- **Eliminated N+1 queries** - Bulk album photo endpoint (`GET /api/albums/{id}/photos`)
- **Total impact**: ~350+ lines removed, cleaner codebase, faster album loading

## Not Implemented (Future Enhancements)
- Video support
- Multi-user authentication
- Upload functionality (only manages existing photos)
- Advanced duplicate detection (perceptual hashing)
- Mobile responsive design
- Light theme toggle

## Testing Checklist
- [ ] Docker build succeeds
- [ ] Container starts without errors
- [ ] Database initialized correctly
- [ ] Initial scan works with sample photos
- [ ] Folder tree renders correctly
- [ ] Photo thumbnails display
- [ ] Lightbox navigation works
- [ ] Album/tag creation works
- [ ] Search functionality works
- [ ] Recycle bin delete/restore works
- [ ] RAW photos display correctly

## Development Workflow

### Running Locally (Without Docker)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export PHOTOS_PATH=./photos
export DATABASE_PATH=./data/metadata/photos.db
export THUMBNAIL_PATH=./data/cache/thumbnails
# Recycle bin uses soft-delete in database
uvicorn backend.main:app --reload
```

### Running with Docker
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Making Changes
- Backend changes require container restart
- Frontend changes (HTML/JS/CSS) are instant (refresh browser)
- No build step required

## Important Notes

- Photos identified by SHA256 hash - renaming/moving preserves metadata
- Deleted photos use soft-delete (`deleted_at` timestamp) - files stay in place until "Empty Recycle Bin"
- Duplicate photos (same hash) automatically skipped during scan
- RAW thumbnail generation slower (1-3s vs <500ms for JPEG)

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/api/health
- Stats: http://localhost:8000/api/stats

## File Structure

```
photo_manager/
├── backend/           # Python FastAPI application
├── frontend/          # Alpine.js + Tailwind frontend
├── data/              # Persistent data (Docker volume)
├── photos/            # Your photos (mount point)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── SPECIFICATIONS.md  # Full project specifications
```

## Next Steps

1. Test Docker build
2. Add sample photos to test with
3. Test all core functionality
4. Performance testing with larger photo libraries
5. Consider adding more sophisticated error handling
6. Add logging configuration
- dont start/build the docker container on your own