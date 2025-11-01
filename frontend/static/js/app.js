/**
 * Photo Manager Alpine.js Application
 */

/**
 * Photo Manager - Main Alpine.js Application
 *
 * A single-file application for managing photos with folders, albums, and tags.
 * Uses Alpine.js for reactive state management with zero build tools.
 */
function photoManager() {
    return {
        // ========================================
        // STATE (Lines 7-50)
        // ========================================
        // Application state variables and modal flags
        authenticated: false,
        folderTree: null,
        expandedFolders: new Set(),
        currentFolder: null,
        currentAlbum: null,
        currentTag: null,
        currentView: 'all',
        currentViewLabel: 'All Photos',

        photos: [],
        folders: [],
        albums: [],
        tags: [],

        currentPage: 1,
        totalPages: 1,
        pageSize: 50,

        selectedPhoto: null,
        lightboxOpen: false,

        searchQuery: '',
        searchTimeout: null,

        recycleBinCount: 0,

        // Modals
        showCreateAlbum: false,
        showCreateTag: false,
        showCreateFolder: false,
        showAddToAlbum: false,
        showAddTag: false,
        newAlbumName: '',
        newAlbumDescription: '',
        newTagName: '',
        newFolderPath: '',
        newFolderParent: '',
        selectedPhotoForAlbum: null,
        selectedPhotoForTag: null,
        photoAlbums: [],  // Array of album IDs the current photo belongs to
        photoTags: [],    // Array of tag IDs the current photo has
        pendingAlbumChanges: { add: [], remove: [] },
        pendingTagChanges: { add: [], remove: [] },

        // Multi-selection
        selectedPhotos: new Set(),
        isSelecting: false,

        // Confirmation modal
        showConfirmModal: false,
        confirmTitle: '',
        confirmMessage: '',
        confirmCallback: null,

        // Inline creation in modals
        showInlineAlbumCreate: false,
        inlineAlbumName: '',
        inlineAlbumDescription: '',
        showInlineTagCreate: false,
        inlineTagName: '',

        // Toast notifications
        toasts: [],
        toastId: 0,

        // ========================================
        // INITIALIZATION
        // ========================================
        async init() {
            console.log('Initializing Photo Manager...');

            // Check authentication first
            await this.checkAuth();

            if (!this.authenticated) {
                console.log('Not authenticated, waiting for login...');
                return;
            }

            await this.loadFolderTree();
            this.expandFirstLevel();
            await this.loadAlbums();
            await this.loadTags();
            await this.selectFolder(''); // Load root folder instead of all photos
            await this.updateRecycleBinCount();
            console.log('Photo Manager initialized');
        },

        // ========================================
        // AUTHENTICATION
        // ========================================
        async checkAuth() {
            try {
                const response = await fetch('/auth/me');
                const data = await response.json();
                this.authenticated = data.authenticated;

                if (!this.authenticated) {
                    console.log('User not authenticated');
                }
            } catch (error) {
                console.error('Auth check failed:', error);
                this.authenticated = false;
            }
        },

        login() {
            window.location.href = '/auth/login';
        },

        async logout() {
            try {
                await fetch('/auth/logout', { method: 'POST' });
                this.authenticated = false;
                // Reload page to clear all state
                window.location.reload();
            } catch (error) {
                console.error('Logout failed:', error);
            }
        },

        // ========================================
        // FOLDER TREE & NAVIGATION (~180 lines)
        // ========================================
        // Handles folder tree rendering, navigation, and folder operations
        async loadFolderTree() {
            try {
                const response = await fetch('/api/folders');
                this.folderTree = await response.json();
            } catch (error) {
                console.error('Error loading folder tree:', error);
            }
        },

        expandFirstLevel() {
            // Don't auto-expand any folders - just make sure the tree is loaded
            // The root is hidden, so first-level folders (Wallpaper, etc.) will be visible but collapsed
        },

        renderFolderTree(node, level = 0, isRootSkip = false) {
            // Skip rendering the root "Photos" folder, directly render its children
            if (level === 0 && !isRootSkip && node.children) {
                let html = '';
                for (const child of node.children) {
                    html += this.renderFolderTree(child, 0, true);
                }
                return html;
            }

            const indent = level * 12;
            const isExpanded = this.expandedFolders.has(node.path);
            const isActive = this.currentFolder === node.path;
            const hasChildren = node.children && node.children.length > 0;

            let html = `
                <div>
                    <div
                        @click="selectFolder('${node.path.replace(/'/g, "\\'")}')"
                        @dragover.prevent="$event.currentTarget.classList.add('bg-blue-600')"
                        @dragleave="$event.currentTarget.classList.remove('bg-blue-600')"
                        @drop.prevent="handleDrop($event, '${node.path.replace(/'/g, "\\'")}')"
                        class="px-3 py-2 hover:bg-gray-700 cursor-pointer rounded transition ${isActive ? 'bg-gray-700 text-blue-400' : ''}"
                        style="padding-left: ${indent + 12}px;">
                        ${hasChildren ? `<span @click.stop="toggleFolder('${node.path.replace(/'/g, "\\'")}') " class="inline-block w-4">${isExpanded ? '▼' : '▶'}</span>` : '<span class="inline-block w-4"></span>'}
                        <span>${node.name}</span>
                        <span class="text-xs text-gray-500 ml-1">(${node.photo_count})</span>
                    </div>
            `;

            if (hasChildren && isExpanded) {
                for (const child of node.children) {
                    html += this.renderFolderTree(child, level + 1, true);
                }
            }

            html += '</div>';
            return html;
        },

        toggleFolder(path) {
            if (this.expandedFolders.has(path)) {
                this.expandedFolders.delete(path);
            } else {
                this.expandedFolders.add(path);
            }
            // Force re-render by updating the folder tree
            this.folderTree = {...this.folderTree};
        },

        async selectFolder(path) {
            this.currentFolder = path;
            this.currentAlbum = null;
            this.currentTag = null;
            this.currentView = 'folder';
            this.currentViewLabel = path || 'Photos';
            this.currentPage = 1;

            // Auto-expand folder tree to show current path
            this.expandFolderPath(path);

            await this.loadFolderPhotos(path);
        },

        expandFolderPath(path) {
            if (!path) {
                // At root, nothing to expand
                return;
            }

            // Expand all parent folders in the path
            const parts = path.split('/');
            let currentPath = '';

            for (let i = 0; i < parts.length; i++) {
                currentPath = i === 0 ? parts[i] : `${currentPath}/${parts[i]}`;

                // Expand all folders except the last one (current folder)
                // Actually, let's expand all including current so subfolders are visible
                if (!this.expandedFolders.has(currentPath)) {
                    this.expandedFolders.add(currentPath);
                }
            }

            // Force re-render
            this.folderTree = {...this.folderTree};
        },
        
        getBreadcrumbs() {
            if (!this.currentFolder) return [];
            
            const parts = this.currentFolder.split('/');
            const breadcrumbs = [];
            let currentPath = '';
            
            for (const part of parts) {
                currentPath = currentPath ? `${currentPath}/${part}` : part;
                breadcrumbs.push({
                    name: part,
                    path: currentPath
                });
            }
            
            return breadcrumbs;
        },
        
        browseUp() {
            if (!this.currentFolder) return;
            
            const parts = this.currentFolder.split('/');
            parts.pop(); // Remove last part
            const parentPath = parts.join('/');
            
            this.selectFolder(parentPath);
        },

        async loadFolderPhotos(path) {
            try {
                const response = await fetch(`/api/folders/${path}?page=${this.currentPage}&limit=${this.pageSize}`);
                const data = await response.json();
                this.photos = data.photos;
                this.totalPages = data.total_pages;
                
                // Load subfolders from the folder tree
                this.folders = this._getSubfolders(path);
            } catch (error) {
                console.error('Error loading folder photos:', error);
            }
        },
        
        _getSubfolders(path) {
            // Find the current folder node in the tree
            const findNode = (node, targetPath) => {
                if (node.path === targetPath) {
                    return node;
                }
                if (node.children) {
                    for (const child of node.children) {
                        const found = findNode(child, targetPath);
                        if (found) return found;
                    }
                }
                return null;
            };
            
            if (!this.folderTree) return [];
            
            const currentNode = findNode(this.folderTree, path);
            return currentNode && currentNode.children ? currentNode.children : [];
        },

        async createFolder() {
            if (!this.newFolderPath.trim()) {
                this.showToast('Please enter a folder name', 'warning');
                return;
            }

            // Build full path
            let fullPath = this.newFolderPath.trim();
            if (this.newFolderParent) {
                fullPath = this.newFolderParent + '/' + fullPath;
            }

            try {
                const response = await fetch('/api/folders', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: fullPath })
                });

                if (response.ok) {
                    await this.loadFolderTree();

                    // Refresh the current view to show the new folder
                    if (this.currentView === 'folder') {
                        await this.loadFolderPhotos(this.currentFolder);
                    }

                    this.showCreateFolder = false;
                    this.newFolderPath = '';
                    this.newFolderParent = '';
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to create folder', 'error');
                }
            } catch (error) {
                console.error('Error creating folder:', error);
                this.showToast('Failed to create folder', 'error');
            }
        },

        openCreateFolderModal(parentPath = '') {
            this.newFolderParent = parentPath;
            this.newFolderPath = '';
            this.showCreateFolder = true;
        },

        async deleteFolder(folderPath) {
            this.showConfirm(
                'Delete Folder',
                `Delete empty folder "${folderPath}"?`,
                async () => {
                    await this.deleteFolderExecute(folderPath);
                }
            );
        },

        async deleteFolderExecute(folderPath) {
            try {
                const response = await fetch(`/api/folders/${folderPath}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    // Reload folder tree
                    await this.loadFolderTree();

                    // Refresh current view if we're in a folder
                    if (this.currentView === 'folder') {
                        await this.loadFolderPhotos(this.currentFolder);
                    }

                    this.showToast('Folder deleted successfully', 'success');
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to delete folder');
                }
            } catch (error) {
                console.error('Error deleting folder:', error);
                this.showToast('Failed to delete folder', 'error');
            }
        },

        // ========================================
        // DRAG AND DROP (~55 lines)
        // ========================================
        // Photo drag-and-drop functionality for folders, albums, and tags
        handleDragStart(event, photoId) {
            event.dataTransfer.effectAllowed = 'move';

            // Check if dragging multiple photos or single
            let draggedPhotos = [];
            if (this.selectedPhotos.has(photoId) && this.selectedPhotos.size > 0) {
                // Dragging multiple selected photos
                draggedPhotos = Array.from(this.selectedPhotos);
            } else {
                // Dragging single photo
                draggedPhotos = [photoId];
            }

            event.dataTransfer.setData('photoIds', JSON.stringify(draggedPhotos));

            // Add dragging class to original element
            event.target.classList.add('dragging');

            // Create custom drag image for multiple photos (stacked appearance)
            if (draggedPhotos.length > 1) {
                const dragContainer = document.createElement('div');
                dragContainer.style.cssText = 'position:absolute;top:-10000px;left:-10000px;';

                // Create stacked photos effect
                const stackContainer = document.createElement('div');
                stackContainer.style.cssText = 'position:relative;width:120px;height:120px;';

                // Show up to 3 stacked photos for visual effect
                const stackCount = Math.min(3, draggedPhotos.length);
                for (let i = 0; i < stackCount; i++) {
                    const stackedImg = document.createElement('div');
                    const offset = i * 4;
                    stackedImg.style.cssText = `
                        position:absolute;
                        top:${offset}px;
                        left:${offset}px;
                        width:100px;
                        height:100px;
                        background:#1f2937;
                        border:3px solid #3b82f6;
                        border-radius:8px;
                        box-shadow:0 4px 8px rgba(0,0,0,0.3);
                        overflow:hidden;
                    `;

                    // For the top layer, try to use the actual image
                    if (i === stackCount - 1) {
                        const img = event.target.querySelector('img');
                        if (img && img.complete && img.src) {
                            // Image is loaded, use it as background
                            stackedImg.style.backgroundImage = `url(${img.src})`;
                            stackedImg.style.backgroundSize = 'cover';
                            stackedImg.style.backgroundPosition = 'center';
                            stackedImg.style.background = `#1f2937 url(${img.src}) center/cover no-repeat`;
                        } else {
                            // Image not loaded or not available, use icon
                            stackedImg.innerHTML = `
                                <svg style="width:50px;height:50px;margin:25px;color:#9ca3af;" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/>
                                </svg>
                            `;
                        }
                    }

                    stackContainer.appendChild(stackedImg);
                }

                // Add count badge
                const badge = document.createElement('div');
                badge.textContent = `${draggedPhotos.length}`;
                badge.style.cssText = `
                    position:absolute;
                    top:-8px;
                    right:-8px;
                    background:#3b82f6;
                    color:white;
                    width:32px;
                    height:32px;
                    border-radius:50%;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-weight:bold;
                    font-size:14px;
                    border:3px solid white;
                    box-shadow:0 2px 4px rgba(0,0,0,0.3);
                `;
                stackContainer.appendChild(badge);

                dragContainer.appendChild(stackContainer);
                document.body.appendChild(dragContainer);

                // Set the custom drag image
                event.dataTransfer.setDragImage(stackContainer, 60, 60);

                // Remove the drag container after a short delay
                setTimeout(() => dragContainer.remove(), 100);
            } else {
                // Single photo drag - create a simple drag image
                const img = event.target.querySelector('img');
                if (img) {
                    const dragImage = document.createElement('div');
                    dragImage.className = 'drag-ghost';
                    dragImage.style.cssText = `
                        position:absolute;
                        top:-1000px;
                        left:-1000px;
                        width:80px;
                        height:80px;
                        border-radius:8px;
                        border:2px solid #3b82f6;
                        overflow:hidden;
                        box-shadow:0 4px 8px rgba(0,0,0,0.3);
                        background:#1f2937;
                    `;

                    // Use background image if available
                    if (img.complete && img.src) {
                        dragImage.style.backgroundImage = `url(${img.src})`;
                        dragImage.style.backgroundSize = 'cover';
                        dragImage.style.backgroundPosition = 'center';
                    } else {
                        // Show icon if image not loaded
                        dragImage.innerHTML = `
                            <svg style="width:40px;height:40px;margin:20px;color:#9ca3af;" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"/>
                            </svg>
                        `;
                    }

                    document.body.appendChild(dragImage);

                    // Set the custom drag image (offset to center under cursor)
                    event.dataTransfer.setDragImage(dragImage, 40, 40);

                    // Remove the temporary drag image after a short delay
                    setTimeout(() => {
                        dragImage.remove();
                    }, 100);
                }
            }
        },

        handleDragEnd(event) {
            event.target.classList.remove('dragging');
        },

        async handleDrop(event, folderPath) {
            event.currentTarget.classList.remove('bg-blue-600');
            const photoIdsJson = event.dataTransfer.getData('photoIds');
            if (photoIdsJson) {
                const photoIds = JSON.parse(photoIdsJson);
                for (const photoId of photoIds) {
                    await this.movePhoto(photoId, folderPath);
                }
                this.clearSelection();
            }
        },

        async handleDropOnAlbum(event, albumId) {
            event.currentTarget.classList.remove('bg-blue-600');
            const photoIdsJson = event.dataTransfer.getData('photoIds');
            if (photoIdsJson) {
                const photoIds = JSON.parse(photoIdsJson);
                for (const photoId of photoIds) {
                    await this.addPhotoToAlbum(photoId, albumId);
                }
                this.clearSelection();
            }
        },

        async handleDropOnTag(event, tagId) {
            event.currentTarget.classList.remove('bg-green-600');
            const photoIdsJson = event.dataTransfer.getData('photoIds');
            if (photoIdsJson) {
                const photoIds = JSON.parse(photoIdsJson);
                for (const photoId of photoIds) {
                    await this.addPhotoToTag(photoId, tagId);
                }
                this.clearSelection();
            }
        },

        async handleDropOnRecycleBin(event) {
            event.currentTarget.classList.remove('bg-red-600');
            const photoIdsJson = event.dataTransfer.getData('photoIds');
            if (photoIdsJson) {
                const photoIds = JSON.parse(photoIdsJson);
                const count = photoIds.length;
                const message = count === 1
                    ? 'Are you sure you want to move this photo to the recycle bin?'
                    : `Are you sure you want to move ${count} photos to the recycle bin?`;

                this.showConfirm(
                    'Move to Recycle Bin',
                    message,
                    async () => {
                        for (const photoId of photoIds) {
                            await this.deletePhotoSilent(photoId);
                        }
                        this.clearSelection();
                    }
                );
            }
        },

        // ========================================
        // ALBUMS (~70 lines)
        // ========================================
        // Album loading, creation, and selection
        async loadAlbums() {
            try {
                const response = await fetch('/api/albums');
                this.albums = await response.json();
            } catch (error) {
                console.error('Error loading albums:', error);
            }
        },

        async selectAlbum(albumId) {
            this.currentAlbum = albumId;
            this.currentFolder = null;
            this.currentTag = null;
            this.currentView = 'album';

            const album = this.albums.find(a => a.id === albumId);
            this.currentViewLabel = album ? `Album: ${album.name}` : 'Album';

            this.currentPage = 1;
            await this.loadAlbumPhotos(albumId);
        },

        async loadAlbumPhotos(albumId) {
            try {
                // Use bulk endpoint to fetch all photos in one request
                const response = await fetch(`/api/albums/${albumId}/photos`);
                const data = await response.json();

                this.photos = data.photos;
                this.folders = []; // Clear folders when viewing album
                this.totalPages = 1;
            } catch (error) {
                console.error('Error loading album photos:', error);
            }
        },

        async createAlbum() {
            if (!this.newAlbumName.trim()) {
                this.showToast('Please enter an album name');
                return;
            }

            try {
                const response = await fetch('/api/albums', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.newAlbumName,
                        description: this.newAlbumDescription
                    })
                });

                if (response.ok) {
                    await this.loadAlbums();
                    this.showCreateAlbum = false;
                    this.newAlbumName = '';
                    this.newAlbumDescription = '';
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to create album');
                }
            } catch (error) {
                console.error('Error creating album:', error);
                this.showToast('Failed to create album');
            }
        },

        // ========================================
        // TAGS (~60 lines)
        // ========================================
        // Tag loading, creation, and selection
        async loadTags() {
            try {
                const response = await fetch('/api/tags');
                this.tags = await response.json();
            } catch (error) {
                console.error('Error loading tags:', error);
            }
        },

        async selectTag(tagId) {
            this.currentTag = tagId;
            this.currentFolder = null;
            this.currentAlbum = null;
            this.currentView = 'tag';

            const tag = this.tags.find(t => t.id === tagId);
            this.currentViewLabel = tag ? `Tag: ${tag.name}` : 'Tag';

            this.currentPage = 1;
            await this.loadTagPhotos(tag.name);
        },

        async loadTagPhotos(tagName) {
            try {
                const response = await fetch(`/api/search?tags=${encodeURIComponent(tagName)}&page=${this.currentPage}&limit=${this.pageSize}`);
                const data = await response.json();
                this.photos = data.photos;
                this.folders = []; // Clear folders when viewing tags
                this.totalPages = data.total_pages;
            } catch (error) {
                console.error('Error loading tag photos:', error);
            }
        },

        async createTag() {
            if (!this.newTagName.trim()) {
                this.showToast('Please enter a tag name');
                return;
            }

            try {
                const response = await fetch('/api/tags', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: this.newTagName })
                });

                if (response.ok) {
                    await this.loadTags();
                    this.showCreateTag = false;
                    this.newTagName = '';
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to create tag');
                }
            } catch (error) {
                console.error('Error creating tag:', error);
                this.showToast('Failed to create tag');
            }
        },

        // ========================================
        // QUICK ADD TO ALBUM/TAG (~120 lines)
        // ========================================
        // Modal dialogs for batch adding/removing photos to/from albums and tags
        // Refactored to use new efficient backend APIs
        async openAddAlbum(photo) {
            this.selectedPhotoForAlbum = photo;
            this.pendingAlbumChanges = { add: [], remove: [] };
            await this.loadPhotoAlbums(photo.id);
            this.showAddToAlbum = true;
        },

        async openAddTag(photo) {
            this.selectedPhotoForTag = photo;
            this.pendingTagChanges = { add: [], remove: [] };
            await this.loadPhotoTags(photo.id);
            this.showAddTag = true;
        },

        async loadPhotoAlbums(photoId) {
            try {
                // Use new efficient API endpoint (1 call instead of N calls)
                const response = await fetch(`/api/photos/${photoId}/albums`);
                const data = await response.json();

                // Extract album IDs
                this.photoAlbums = data.albums.map(album => album.id);
            } catch (error) {
                console.error('Error loading photo albums:', error);
                this.photoAlbums = [];
            }
        },

        async loadPhotoTags(photoId) {
            try {
                // Use new efficient API endpoint (1 call instead of N calls)
                const response = await fetch(`/api/photos/${photoId}/tags`);
                const data = await response.json();

                // Extract tag IDs
                this.photoTags = data.tags.map(tag => tag.id);
            } catch (error) {
                console.error('Error loading photo tags:', error);
                this.photoTags = [];
            }
        },

        // Generic toggle function for both albums and tags
        _toggleCollection(collectionId, currentList, pendingChanges) {
            const isCurrentlyInCollection = currentList.includes(collectionId);

            if (isCurrentlyInCollection) {
                // Mark for removal
                const newList = currentList.filter(id => id !== collectionId);

                // Track this change
                if (pendingChanges.add.includes(collectionId)) {
                    pendingChanges.add = pendingChanges.add.filter(id => id !== collectionId);
                } else if (!pendingChanges.remove.includes(collectionId)) {
                    pendingChanges.remove.push(collectionId);
                }

                return newList;
            } else {
                // Mark for addition
                const newList = [...currentList, collectionId];

                // Track this change
                if (pendingChanges.remove.includes(collectionId)) {
                    pendingChanges.remove = pendingChanges.remove.filter(id => id !== collectionId);
                } else if (!pendingChanges.add.includes(collectionId)) {
                    pendingChanges.add.push(collectionId);
                }

                return newList;
            }
        },

        async togglePhotoInAlbum(albumId) {
            if (!this.selectedPhotoForAlbum) return;
            this.photoAlbums = this._toggleCollection(albumId, this.photoAlbums, this.pendingAlbumChanges);
        },

        async togglePhotoTag(tagId) {
            if (!this.selectedPhotoForTag) return;
            this.photoTags = this._toggleCollection(tagId, this.photoTags, this.pendingTagChanges);
        },

        // Generic function to apply collection changes (albums or tags)
        async _applyCollectionChanges(collectionType, photoId, pendingChanges, reloadFunction) {
            const isAlbum = collectionType === 'albums';
            const basePath = isAlbum ? '/api/albums' : '/api/tags';

            try {
                // Apply all removals
                for (const collectionId of pendingChanges.remove) {
                    const response = await fetch(`${basePath}/${collectionId}/photos/${photoId}`, {
                        method: 'DELETE'
                    });

                    if (!response.ok) {
                        const error = await response.json();
                        this.showToast(error.detail || `Failed to remove photo from ${collectionType}`);
                        return false;
                    }
                }

                // Apply all additions
                for (const collectionId of pendingChanges.add) {
                    const response = await fetch(`${basePath}/${collectionId}/photos`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ photo_ids: [photoId] })
                    });

                    if (!response.ok) {
                        const error = await response.json();
                        this.showToast(error.detail || `Failed to add photo to ${collectionType}`);
                        return false;
                    }
                }

                // Refresh the view and reload counts
                await this.refreshCurrentView();
                await reloadFunction();

                return true;
            } catch (error) {
                console.error(`Error applying ${collectionType} changes:`, error);
                this.showToast(`Failed to update ${collectionType}`);
                return false;
            }
        },

        async applyAlbumChanges() {
            if (!this.selectedPhotoForAlbum) return;

            const success = await this._applyCollectionChanges(
                'albums',
                this.selectedPhotoForAlbum.id,
                this.pendingAlbumChanges,
                () => this.loadAlbums()
            );

            if (success) {
                this.showAddToAlbum = false;
            }
        },

        async applyTagChanges() {
            if (!this.selectedPhotoForTag) return;

            const success = await this._applyCollectionChanges(
                'tags',
                this.selectedPhotoForTag.id,
                this.pendingTagChanges,
                () => this.loadTags()
            );

            if (success) {
                this.showAddTag = false;
            }
        },

        async refreshCurrentView() {
            // Refresh the current view to reflect changes
            if (this.currentView === 'folder') {
                await this.selectFolder(this.currentFolder);
            } else if (this.currentView === 'album') {
                await this.selectAlbum(this.currentAlbum);
            } else if (this.currentView === 'tag') {
                await this.selectTag(this.currentTag);
            } else if (this.currentView === 'all') {
                await this.loadAllPhotos();
            } else if (this.currentView === 'search') {
                await this.doSearch();
            } else if (this.currentView === 'recycle-bin') {
                await this.loadRecycleBin();
            }
        },

        // ========================================
        // DRAG & DROP HELPERS (~50 lines)
        // ========================================
        // Quick add functions for drag-and-drop operations
        async addPhotoToAlbum(photoId, albumId) {
            try {
                const response = await fetch(`/api/albums/${albumId}/photos`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ photo_ids: [photoId] })
                });

                if (response.ok) {
                    const album = this.albums.find(a => a.id === albumId);
                    console.log(`Photo added to album: ${album?.name || albumId}`);
                    
                    // Reload album counts
                    await this.loadAlbums();
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to add photo to album');
                }
            } catch (error) {
                console.error('Error adding photo to album:', error);
                this.showToast('Failed to add photo to album');
            }
        },

        async addPhotoToTag(photoId, tagId) {
            try {
                const response = await fetch(`/api/tags/${tagId}/photos`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ photo_ids: [photoId] })
                });

                if (response.ok) {
                    const tag = this.tags.find(t => t.id === tagId);
                    console.log(`Tag added to photo: ${tag?.name || tagId}`);
                    
                    // Reload tag counts
                    await this.loadTags();
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to add tag to photo');
                }
            } catch (error) {
                console.error('Error adding tag to photo:', error);
                this.showToast('Failed to add tag to photo');
            }
        },

        // ========================================
        // PHOTOS, SEARCH & PAGINATION (~70 lines)
        // ========================================
        async loadPhotos() {
            try {
                const response = await fetch(`/api/photos?page=${this.currentPage}&limit=${this.pageSize}`);
                const data = await response.json();
                this.photos = data.photos;
                this.totalPages = data.total_pages;
                this.currentView = 'all';
                this.currentViewLabel = 'All Photos';
            } catch (error) {
                console.error('Error loading photos:', error);
            }
        },

        performSearch() {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(async () => {
                if (this.searchQuery.trim()) {
                    this.currentView = 'search';
                    this.currentViewLabel = `Search: ${this.searchQuery}`;
                    this.currentPage = 1;
                    await this.searchPhotos();
                } else {
                    await this.loadPhotos();
                }
            }, 300);
        },

        async searchPhotos() {
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(this.searchQuery)}&page=${this.currentPage}&limit=${this.pageSize}`);
                const data = await response.json();
                this.photos = data.photos;
                this.folders = []; // Clear folders when searching
                this.totalPages = data.total_pages;
            } catch (error) {
                console.error('Error searching photos:', error);
            }
        },

        async changePage(page) {
            if (page < 1 || page > this.totalPages) return;

            this.currentPage = page;

            if (this.currentView === 'folder') {
                await this.loadFolderPhotos(this.currentFolder);
            } else if (this.currentView === 'album') {
                await this.loadAlbumPhotos(this.currentAlbum);
            } else if (this.currentView === 'tag') {
                const tag = this.tags.find(t => t.id === this.currentTag);
                await this.loadTagPhotos(tag.name);
            } else if (this.currentView === 'search') {
                await this.searchPhotos();
            } else {
                await this.loadPhotos();
            }
        },

        // ========================================
        // LIGHTBOX (~30 lines)
        // ========================================
        // Full-screen photo viewer with keyboard navigation
        openLightbox(photo) {
            this.selectedPhoto = photo;
            this.lightboxOpen = true;
        },

        closeLightbox() {
            this.lightboxOpen = false;
            this.selectedPhoto = null;
        },

        previousPhoto() {
            if (!this.selectedPhoto || !this.lightboxOpen) return;
            const index = this.photos.findIndex(p => p.id === this.selectedPhoto.id);
            if (index > 0) {
                this.selectedPhoto = this.photos[index - 1];
            }
        },

        nextPhoto() {
            if (!this.selectedPhoto || !this.lightboxOpen) return;
            const index = this.photos.findIndex(p => p.id === this.selectedPhoto.id);
            if (index < this.photos.length - 1) {
                this.selectedPhoto = this.photos[index + 1];
            }
        },

        // ========================================
        // PHOTO OPERATIONS (~55 lines)
        // ========================================
        // Move and delete photo operations
        async movePhoto(photoId, folderPath) {
            try {
                const response = await fetch(`/api/photos/${photoId}/move`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ folder_path: folderPath })
                });

                if (response.ok) {
                    // Reload current view and folder tree
                    if (this.currentView === 'folder') {
                        await this.loadFolderPhotos(this.currentFolder);
                    } else {
                        await this.loadPhotos();
                    }
                    await this.loadFolderTree();
                    return true;
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to move photo');
                    return false;
                }
            } catch (error) {
                console.error('Error moving photo:', error);
                this.showToast('Failed to move photo');
                return false;
            }
        },

        async deletePhoto(photoId) {
            this.showConfirm(
                'Move to Recycle Bin',
                'Are you sure you want to move this photo to the recycle bin?',
                async () => {
                    await this.deletePhotoSilent(photoId);
                }
            );
        },

        async deletePhotoSilent(photoId) {
            try {
                const response = await fetch(`/api/photos/${photoId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    this.closeLightbox();
                    // Reload current view
                    if (this.currentView === 'folder') {
                        await this.loadFolderPhotos(this.currentFolder);
                    } else {
                        await this.loadPhotos();
                    }
                    await this.updateRecycleBinCount();
                    await this.loadFolderTree();
                } else {
                    this.showToast('Failed to delete photo');
                }
            } catch (error) {
                console.error('Error deleting photo:', error);
                this.showToast('Failed to delete photo');
            }
        },

        // ========================================
        // RECYCLE BIN (~65 lines)
        // ========================================
        // Soft-delete functionality with restore support
        async viewRecycleBin() {
            this.currentView = 'recycle-bin';
            this.currentViewLabel = 'Recycle Bin';
            this.currentFolder = null;
            this.currentAlbum = null;
            this.currentTag = null;

            try {
                const response = await fetch('/api/recycle-bin');
                const data = await response.json();
                // Map recycle bin items to photo format
                this.photos = data.photos.map(p => ({
                    id: p.id,
                    filename: p.filename,
                    isDeleted: true
                }));
                this.folders = []; // Clear folders when viewing recycle bin
                this.totalPages = 1;
            } catch (error) {
                console.error('Error loading recycle bin:', error);
            }
        },

        async updateRecycleBinCount() {
            try {
                const response = await fetch('/api/recycle-bin');
                const data = await response.json();
                this.recycleBinCount = data.count;
            } catch (error) {
                console.error('Error updating recycle bin count:', error);
            }
        },

        async restorePhoto(photo) {
            this.showConfirm(
                'Restore Photo',
                `Are you sure you want to restore "${photo.filename}"?`,
                async () => {
                    await this.restorePhotoExecute(photo);
                }
            );
        },

        async restorePhotoExecute(photo) {
            try {
                const response = await fetch(`/api/recycle-bin/${photo.id}/restore`, {
                    method: 'POST'
                });

                if (response.ok) {
                    // Remove photo from current view
                    this.photos = this.photos.filter(p => p.id !== photo.id);

                    // Update recycle bin count
                    await this.updateRecycleBinCount();
                    await this.loadFolderTree();

                    this.showToast('Photo restored successfully!');
                    console.log('Photo restored successfully');
                } else {
                    const error = await response.json();
                    console.error('Restore error:', error);
                    this.showToast(`Failed to restore photo:\n${error.detail || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error restoring photo:', error);
                this.showToast('Failed to restore photo: ' + error.message);
            }
        },

        async emptyRecycleBin() {
            this.showConfirm(
                'Empty Recycle Bin',
                `Are you sure you want to permanently delete all ${this.recycleBinCount} photos from the recycle bin? This action cannot be undone!`,
                async () => {
                    await this.emptyRecycleBinExecute();
                }
            );
        },

        async emptyRecycleBinExecute() {
            try {
                const response = await fetch('/api/recycle-bin/empty', {
                    method: 'DELETE'
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    // Clear photos from view
                    this.photos = [];
                    
                    // Update recycle bin count
                    await this.updateRecycleBinCount();
                    await this.loadFolderTree();

                    this.showToast(`Successfully deleted ${data.count} photos permanently!`);
                    console.log('Recycle bin emptied:', data);
                } else {
                    const error = await response.json();
                    console.error('Empty recycle bin error:', error);
                    this.showToast(`Failed to empty recycle bin: ${error.detail || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error emptying recycle bin:', error);
                this.showToast('Failed to empty recycle bin: ' + error.message);
            }
        },

        // ========================================
        // SYSTEM OPERATIONS (~30 lines)
        // ========================================
        // Library scanning and system-level operations
        async scanLibrary() {
            this.showConfirm(
                'Scan Library',
                'Scan library for new photos? This may take a while.',
                async () => {
                    await this.scanLibraryExecute();
                }
            );
        },

        async scanLibraryExecute() {
            try {
                const response = await fetch('/api/photos/scan', { method: 'POST' });
                const data = await response.json();
                this.showToast(`Scan complete!\nScanned: ${data.stats.scanned}\nIndexed: ${data.stats.indexed}\nSkipped: ${data.stats.skipped}`);
                await this.loadPhotos();
                await this.loadFolderTree();
            } catch (error) {
                console.error('Error scanning library:', error);
                this.showToast('Failed to scan library');
            }
        },

        // ========================================
        // CONFIRMATION MODAL
        // ========================================
        showConfirm(title, message, callback) {
            this.confirmTitle = title;
            this.confirmMessage = message;
            this.confirmCallback = callback;
            this.showConfirmModal = true;
        },

        confirmAction() {
            if (this.confirmCallback) {
                this.confirmCallback();
            }
            this.showConfirmModal = false;
            this.confirmCallback = null;
        },

        cancelConfirm() {
            this.showConfirmModal = false;
            this.confirmCallback = null;
        },

        // ========================================
        // TOAST NOTIFICATIONS
        // ========================================
        showToast(message, type = 'info', duration = 3000) {
            const id = ++this.toastId;
            const toast = {
                id,
                message,
                type, // 'success', 'error', 'info', 'warning'
                show: true
            };

            this.toasts.push(toast);

            // Auto-remove after duration
            setTimeout(() => {
                this.removeToast(id);
            }, duration);
        },

        removeToast(id) {
            const index = this.toasts.findIndex(t => t.id === id);
            if (index !== -1) {
                this.toasts.splice(index, 1);
            }
        },

        // ========================================
        // MULTI-SELECTION
        // ========================================
        toggleSelectionMode() {
            this.isSelecting = !this.isSelecting;
            if (!this.isSelecting) {
                this.selectedPhotos.clear();
            }
        },

        togglePhotoSelection(photoId, event) {
            if (event) {
                event.preventDefault();
                event.stopPropagation();
            }

            if (this.selectedPhotos.has(photoId)) {
                this.selectedPhotos.delete(photoId);
            } else {
                this.selectedPhotos.add(photoId);
            }

            // Auto-enable selection mode when first photo is selected
            if (this.selectedPhotos.size > 0 && !this.isSelecting) {
                this.isSelecting = true;
            }
        },

        selectAllPhotos() {
            this.photos.forEach(photo => {
                if (!photo.isDeleted) {
                    this.selectedPhotos.add(photo.id);
                }
            });
        },

        clearSelection() {
            this.selectedPhotos.clear();
        },

        isPhotoSelected(photoId) {
            return this.selectedPhotos.has(photoId);
        },

        // ========================================
        // INLINE CREATION IN MODALS
        // ========================================
        async createAlbumInline() {
            if (!this.inlineAlbumName.trim()) return;

            try {
                const response = await fetch('/api/albums', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.inlineAlbumName.trim(),
                        description: this.inlineAlbumDescription.trim()
                    })
                });

                if (response.ok) {
                    const newAlbum = await response.json();
                    await this.loadAlbums();

                    // Auto-check the newly created album
                    this.photoAlbums.push(newAlbum.id);
                    if (!this.pendingAlbumChanges.add.includes(newAlbum.id)) {
                        this.pendingAlbumChanges.add.push(newAlbum.id);
                    }

                    // Close inline form
                    this.showInlineAlbumCreate = false;
                    this.inlineAlbumName = '';
                    this.inlineAlbumDescription = '';
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to create album');
                }
            } catch (error) {
                console.error('Error creating album:', error);
                this.showToast('Failed to create album');
            }
        },

        async createTagInline() {
            if (!this.inlineTagName.trim()) return;

            try {
                const response = await fetch('/api/tags', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.inlineTagName.trim()
                    })
                });

                if (response.ok) {
                    const newTag = await response.json();
                    await this.loadTags();

                    // Auto-check the newly created tag
                    this.photoTags.push(newTag.id);
                    if (!this.pendingTagChanges.add.includes(newTag.id)) {
                        this.pendingTagChanges.add.push(newTag.id);
                    }

                    // Close inline form
                    this.showInlineTagCreate = false;
                    this.inlineTagName = '';
                } else {
                    const error = await response.json();
                    this.showToast(error.detail || 'Failed to create tag');
                }
            } catch (error) {
                console.error('Error creating tag:', error);
                this.showToast('Failed to create tag');
            }
        },

        formatTimestamp(timestamp) {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
            if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
            if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

            return date.toLocaleString();
        }
    };
}
