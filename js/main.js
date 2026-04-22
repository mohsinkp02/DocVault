import { hfService } from './api/hfService.js?v=3';
import { stateManager } from './state/stateManager.js';
import { UIRenderer } from './ui/uiRenderer.js';
import { getFileUrl, isImage, isPDF, isText } from './utils/formatters.js';

class App {
  constructor() {
    this.ui = new UIRenderer(stateManager, hfService);
    this.state = stateManager;
    this.hf = hfService;
    this.pendingDelete = null;
    this.pendingRename = null;
    this.cachedFolders = [];
    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.setupNetworkHandling();
    this.setupDragAndDrop();
    this.state.subscribe(() => this.render());
    this.fetchAndRender();
  }

  setupNetworkHandling() {
    window.addEventListener('online', () => {
      this.ui.showToast('Back online! Syncing...', 'success');
      this.fetchAndRender();
    });
    window.addEventListener('offline', () => {
      this.ui.showToast('You are offline. Some features may be limited.', 'warning');
    });
  }

  setupDragAndDrop() {
    const area = document.getElementById('contentArea');
    if (!area) return;

    ['dragenter', 'dragover'].forEach(evt => {
      area.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        area.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(evt => {
      area.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        area.classList.remove('drag-over');
      });
    });

    area.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.uploadFiles(files);
      }
    });
  }

  setupEventListeners() {
    // Nav
    document.getElementById('navMyFiles').onclick = (e) => {
      e.preventDefault();
      this.state.setBrowseMode('files');
      this.state.setPath([]);
      this.fetchAndRender();
    };
    document.getElementById('navRecent').onclick = (e) => {
      e.preventDefault();
      this.state.setBrowseMode('recent');
      this.render();
    };
    document.getElementById('navStarred').onclick = (e) => {
      e.preventDefault();
      this.state.setBrowseMode('starred');
      this.render();
    };

    // View Toggles
    document.getElementById('viewGrid').onclick = () => this.state.setViewMode('grid');
    document.getElementById('viewList').onclick = () => this.state.setViewMode('list');

    // Search
    let searchDebounce;
    document.getElementById('searchInput').oninput = (e) => {
      clearTimeout(searchDebounce);
      searchDebounce = setTimeout(() => {
        this.state.setSearchQuery(e.target.value.trim());
        this.fetchAndRender();
      }, 400);
    };

    // New actions
    document.getElementById('newBtn').onclick = (e) => {
      e.stopPropagation();
      document.getElementById('newDropdown').classList.toggle('active');
    };
    document.getElementById('uploadFileBtn').onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      document.getElementById('newDropdown').classList.remove('active');
      document.getElementById('fileInput').click();
    };
    document.getElementById('createFolderBtn').onclick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      document.getElementById('newDropdown').classList.remove('active');
      document.getElementById('createFolderModal').classList.add('active');
      document.getElementById('folderNameInput').value = '';
      document.getElementById('folderNameInput').focus();
    };

    // File Input
    document.getElementById('fileInput').onchange = (e) => {
      this.uploadFiles(e.target.files);
      e.target.value = '';
    };

    // Create Folder Modal
    document.getElementById('confirmFolderBtn').onclick = () => this.createFolder();
    document.getElementById('cancelFolderBtn').onclick = () => document.getElementById('createFolderModal').classList.remove('active');

    // Enter on folder name input
    document.getElementById('folderNameInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.createFolder();
    });

    // Delete Modal
    document.getElementById('confirmDeleteBtn').onclick = () => this.confirmDelete();
    document.getElementById('cancelDeleteBtn').onclick = () => document.getElementById('deleteModal').classList.remove('active');

    // Rename Modal
    document.getElementById('confirmRenameBtn').onclick = () => this.renameItem();
    document.getElementById('cancelRenameBtn').onclick = () => document.getElementById('renameModal').classList.remove('active');
    document.getElementById('renameFromPreview').onclick = () => {
      if (this.currentPreviewFile) this.openRenameModal(this.currentPreviewFile.path, this.currentPreviewFile.name);
    };

    // Enter on rename input
    document.getElementById('renameInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.renameItem();
      if (e.key === 'Escape') document.getElementById('renameModal').classList.remove('active');
    });
    document.addEventListener('click', () => {
      document.getElementById('newDropdown').classList.remove('active');
      // Close all dropdown menus
      document.querySelectorAll('.dropdown-menu.open').forEach(m => m.classList.remove('open'));
    });

    // Mobile Toggle
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.querySelector('.sidebar');
    if (menuToggle && sidebar) {
      menuToggle.onclick = (e) => {
        e.stopPropagation();
        sidebar.classList.toggle('mobile-open');
      };
    }

    // Close sidebar on navigation (mobile)
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        sidebar.classList.remove('mobile-open');
      });
    });

    // Modals Close via X button
    document.querySelectorAll('.close-modal').forEach(btn => {
      btn.onclick = () => {
        btn.closest('.modal-overlay').classList.remove('active');
      };
    });

    // Modals close on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          overlay.classList.remove('active');
          sidebar.classList.remove('mobile-open');
        }
      });
    });

    document.getElementById('downloadFromPreview').onclick = () => {
      if (!this.currentPreviewFile) return;
      const url = this.getPreviewUrl(this.currentPreviewFile.path, true);
      this.downloadFile(url, this.currentPreviewFile.name);
    };
  }

  async fetchAndRender() {
    if (this.state.isFetching) return;
    this.state.isFetching = true;
    this.ui.showSkeletons();

    try {
      const path = this.state.getFolderPath();
      const { files, folders } = await this.hf.listFiles(path);

      this.state.cachedFiles = files;
      this.cachedFolders = folders;
      this.render();
      this.updateStorageStats();
    } catch (err) {
      console.error('Fetch error:', err);
      this.ui.showToast(err.message || 'Failed to load files', 'error');
    } finally {
      this.state.isFetching = false;
    }
  }

  async updateStorageStats() {
    try {
      const { files } = await this.hf.listFiles('', true);
      const totalSize = files.reduce((sum, f) => sum + (f.size || 0), 0);
      const count = files.length;

      document.getElementById('storageUsageText').textContent = `${count} files • ${this.formatSize(totalSize)} used`;
      const MAX_STORAGE = 10 * 1024 * 1024 * 1024; // 10GB
      const pct = Math.min((totalSize / MAX_STORAGE) * 100, 100);
      document.getElementById('storageProgress').style.width = pct + '%';
    } catch (err) {
      console.error('Storage stats error:', err);
    }
  }

  formatSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  render() {
    const browseMode = this.state.currentBrowse;
    let displayFiles = [];
    let displayFolders = [];

    if (browseMode === 'files') {
      displayFiles = this.state.cachedFiles;
      displayFolders = this.cachedFolders;
      this.ui.renderBreadcrumbs((path) => {
        this.state.setPath(path);
        this.fetchAndRender();
      });
    } else if (browseMode === 'recent') {
      displayFiles = this.state.recent;
      document.getElementById('breadcrumbs').innerHTML = '<span class="breadcrumb-item active">Recent</span>';
    } else if (browseMode === 'starred') {
      displayFiles = this.state.cachedFiles.filter(f => this.state.starred.includes(f.path));
      document.getElementById('breadcrumbs').innerHTML = '<span class="breadcrumb-item active">Starred</span>';
    }

    // Filter by search
    if (this.state.searchQuery) {
      const q = this.state.searchQuery.toLowerCase();
      displayFiles = displayFiles.filter(f => f.name.toLowerCase().includes(q));
      displayFolders = displayFolders.filter(f => f.name.toLowerCase().includes(q));
    }

    this.ui.renderFolders(displayFolders, (name) => {
      this.state.setPath([...this.state.currentPath, name]);
      this.fetchAndRender();
    }, (path, name) => this.openRenameModal(path, name), (path, name) => this.openDeleteModal(path, name));

    this.ui.renderFiles(displayFiles, {
      onPreview: (file) => this.openPreview(file),
      onDownload: (url, name) => this.downloadFile(url, name),
      onRename: (path, name) => this.openRenameModal(path, name),
      onStar: (path) => this.state.toggleStar(path),
      onDelete: (path, name) => this.openDeleteModal(path, name),
      onHistory: (path, name) => this.openHistory(path, name),
      getUrl: (path) => getFileUrl(this.hf.apiBase || '/api', path)
    });

    this.updateActiveNavItem();
  }

  updateActiveNavItem() {
    const items = {
      files: 'navMyFiles',
      recent: 'navRecent',
      starred: 'navStarred'
    };
    Object.values(items).forEach(id => document.getElementById(id).classList.remove('active'));
    document.getElementById(items[this.state.currentBrowse]).classList.add('active');
  }

  async uploadFiles(fileList) {
    const files = Array.from(fileList);
    const MAX_SIZE = 10 * 1024 * 1024; // 10MB limit for simple API

    for (const file of files) {
      // 1. Validation
      if (!this.isValidName(file.name)) {
        this.ui.showToast(`Invalid file name: ${file.name}`, 'error');
        continue;
      }

      if (file.size > MAX_SIZE) {
        this.ui.showToast(`File too large: ${file.name} (Max 10MB)`, 'warning');
        continue;
      }

      const path = this.state.getFolderPath();
      const destPath = path ? `${path}/${file.name}` : file.name;

      // 2. Duplicate Check
      if (this.state.cachedFiles.some(f => f.path === destPath)) {
        this.ui.showToast(`File already exists: ${file.name}`, 'warning');
        continue;
      }

      this.ui.showProgress(`Uploading ${file.name}...`);
      try {
        await this.hf.uploadFile(file, destPath);
        this.ui.showToast(`Uploaded ${file.name}`, 'success');
      } catch (err) {
        this.ui.showToast(err.message, 'error');
      }
    }
    this.ui.hideProgress();
    this.fetchAndRender();
  }

  async createFolder() {
    const name = document.getElementById('folderNameInput').value.trim();
    if (!name) return;

    if (!this.isValidName(name)) {
      this.ui.showToast('Invalid folder name', 'error');
      return;
    }

    const path = this.state.getFolderPath();
    const destPath = path ? `${path}/${name}` : name;

    // Check if folder name is already taken
    if (this.cachedFolders.some(f => f.name === name)) {
      this.ui.showToast(`Folder already exists: ${name}`, 'warning');
      return;
    }

    document.getElementById('createFolderModal').classList.remove('active');
    this.ui.showProgress(`Creating folder ${name}...`);
    try {
      await this.hf.createFolder(destPath);
      this.ui.showToast(`Folder "${name}" created`, 'success');
      this.fetchAndRender();
    } catch (err) {
      this.ui.showToast(err.message, 'error');
    } finally {
      this.ui.hideProgress();
    }
  }

  isValidName(name) {
    const forbidden = /[<>:"\\|?*\x00-\x1F]/;
    return name && name.length > 0 && !forbidden.test(name) && name.length < 255;
  }

  openDeleteModal(path, name) {
    this.pendingDelete = path;
    const strong = document.querySelector('#deleteModal p strong');
    if (strong) strong.textContent = name;
    document.getElementById('deleteModal').classList.add('active');
  }

  openRenameModal(path, name) {
    const renameModal = document.getElementById('renameModal');
    const renameInput = document.getElementById('renameInput');
    const renameTitle = document.querySelector('#renameModal h3');
    const isFolder = this.cachedFolders.some(folder => folder.path === path);

    this.pendingRename = {
      path,
      originalName: name,
      itemType: isFolder ? 'folder' : 'file'
    };

    if (renameTitle) {
      renameTitle.innerHTML = `<i class="ph-fill ph-pencil-simple" style="color:var(--primary-color)"></i> Rename ${isFolder ? 'Folder' : 'File'}`;
    }

    if (renameInput) {
      renameInput.value = name;
    }

    renameModal.classList.add('active');
    setTimeout(() => {
      renameInput.focus();
      renameInput.select();
    }, 100);
  }

  getPreviewUrl(path, asDownload = false) {
    const baseUrl = getFileUrl(this.hf.apiBase || window.__DOCVAULT_API_BASE__ || '/api', path);
    return asDownload ? `${baseUrl}?download=true` : baseUrl;
  }

  previewFallback(name, url, message) {
    return `
      <div class="preview-fallback">
        <i class="ph-fill ph-file"></i>
        <p>${message}</p>
        <a href="${url}" target="_blank" rel="noopener noreferrer" class="btn-primary" style="text-decoration:none;display:inline-flex;align-items:center;gap:8px;margin-top:16px">
          <i class="ph-fill ph-download-simple"></i> Open File
        </a>
      </div>
    `;
  }

  async openPreview(file) {
    const previewModal = document.getElementById('previewModal');
    const previewBody = document.getElementById('previewBody');
    const previewFileName = document.getElementById('previewFileName');
    const previewUrl = this.getPreviewUrl(file.path);

    this.currentPreviewFile = file;
    previewFileName.textContent = file.name;
    previewBody.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading preview...</p></div>';
    previewModal.classList.add('active');

    if (isImage(file.name)) {
      const img = new Image();
      img.src = previewUrl;
      img.className = 'preview-image';
      img.onload = () => {
        previewBody.innerHTML = '';
        previewBody.appendChild(img);
      };
      img.onerror = () => {
        previewBody.innerHTML = this.previewFallback(file.name, previewUrl, 'Image preview is unavailable.');
      };
      return;
    }

    if (isPDF(file.name)) {
      previewBody.innerHTML = `<iframe class="preview-iframe" src="${previewUrl}" title="${file.name}"></iframe>`;
      return;
    }

    if (isText(file.name)) {
      try {
        const response = await fetch(previewUrl, { headers: { 'X-User-ID': 'default_user' } });
        if (!response.ok) throw new Error(`Preview failed: ${response.status}`);

        const pre = document.createElement('pre');
        pre.className = 'preview-text';
        pre.textContent = await response.text();
        previewBody.innerHTML = '';
        previewBody.appendChild(pre);
      } catch (err) {
        previewBody.innerHTML = this.previewFallback(file.name, previewUrl, 'Text preview could not be loaded.');
      }
      return;
    }

    previewBody.innerHTML = this.previewFallback(file.name, previewUrl, 'No inline preview is available for this file type.');
  }

  downloadFile(url, name) {
    const link = document.createElement('a');
    link.href = url;
    link.download = name;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  async openHistory(path, name) {
    this.ui.showHistoryModal(name);
    try {
      const history = await this.hf.getHistory(path);
      this.ui.renderHistory(history, async (revision, asCopy) => {
        try {
          const result = await this.hf.restoreVersion(path, revision, asCopy);
          if (!result.success) throw new Error(result.error || 'Restore failed');
          this.ui.showToast(result.message || 'Version restored', 'success');
          this.fetchAndRender();
        } catch (err) {
          this.ui.showToast(err.message || 'Restore failed', 'error');
        }
      });
    } catch (err) {
      this.ui.showToast(err.message || 'Failed to load version history', 'error');
    }
  }

  async confirmDelete() {
    if (!this.pendingDelete) return;
    const path = this.pendingDelete;
    const btn = document.getElementById('confirmDeleteBtn');
    
    // Check if item still exists in local set to avoid stale deletes
    const exists = this.state.cachedFiles.some(f => f.path === path) || this.cachedFolders.some(f => f.path === path);
    if (!exists) {
      this.ui.showToast('Item no longer exists', 'warning');
      this.pendingDelete = null;
      document.getElementById('deleteModal').classList.remove('active');
      return;
    }

    if (btn) btn.classList.add('loading');
    try {
      const isFolder = this.cachedFolders.some(f => f.path === path);
      if (isFolder) {
        await this.hf.deleteFolder(path);
      } else {
        await this.hf.deleteFile(path);
      }
      this.ui.showToast('Deleted successfully', 'success');
      document.getElementById('deleteModal').classList.remove('active');
      this.pendingDelete = null;
      this.fetchAndRender();
    } catch (err) {
      this.ui.showToast(err.message || 'Delete failed', 'error');
    } finally {
      if (btn) btn.classList.remove('loading');
    }
  }

  async renameItem() {
    if (!this.pendingRename) return;
    
    const newNameInput = document.getElementById('renameInput');
    const btn = document.getElementById('confirmRenameBtn');
    if (!newNameInput || !btn) return;
    
    const newName = newNameInput.value.trim();
    if (!newName) {
      this.ui.showToast('Please enter a new name', 'warning');
      return;
    }
    
    if (newName === this.pendingRename.originalName) {
      document.getElementById('renameModal').classList.remove('active');
      this.pendingRename = null;
      return;
    }
    
    if (!this.isValidName(newName)) {
      this.ui.showToast('Invalid name format (avoid < > : " / \\ | ? *)', 'error');
      return;
    }

    // Client-side Conflict Check
    const isConflict = this.state.cachedFiles.some(f => f.name.toLowerCase() === newName.toLowerCase()) || 
                      this.cachedFolders.some(f => f.name.toLowerCase() === newName.toLowerCase());
    
    if (isConflict) {
      this.ui.showToast(`An item with name "${newName}" already exists in this folder`, 'warning');
      return;
    }
    
    const path = this.pendingRename.path;
    const oldName = this.pendingRename.originalName;
    
    btn.classList.add('loading');
    try {
      const res = await this.hf.renameItem(path, newName);
      if (res.success) {
        this.ui.showToast(`Renamed "${oldName}" to "${newName}"`, 'success');
        document.getElementById('renameModal').classList.remove('active');
        this.pendingRename = null;
        this.fetchAndRender();
      } else {
        throw new Error(res.error || 'Rename failed');
      }
    } catch (err) {
      this.ui.showToast(err.message, 'error');
    } finally {
      btn.classList.remove('loading');
    }
  }
}

new App();
