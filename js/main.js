import { hfService } from './api/hfService.js?v=2';
import { stateManager } from './state/stateManager.js';
import { UIRenderer } from './ui/uiRenderer.js';
import { getFileUrl, isImage, isPDF, isText } from './utils/formatters.js';

class App {
  constructor() {
    this.ui = new UIRenderer(stateManager, hfService);
    this.state = stateManager;
    this.hf = hfService;
    this.pendingDelete = null;
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



    // Click outside closes dropdown
    document.addEventListener('click', () => {
      document.getElementById('newDropdown').classList.remove('active');
      // Close all dropdown menus
      document.querySelectorAll('.dropdown-menu.open').forEach(m => m.classList.remove('open'));
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
        }
      });
    });
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
    }, (path, name) => this.openDeleteModal(path, name));

    this.ui.renderFiles(displayFiles, {
      onPreview: (file) => this.openPreview(file),
      onDownload: (url, name) => this.downloadFile(url, name),
      onStar: (path) => this.state.toggleStar(path),
      onDelete: (path, name) => this.openDeleteModal(path, name),
      getUrl: (path) => getFileUrl(this.hf.apiBase, path)
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
      const keepPath = `${destPath}/.gitkeep`;
      await this.hf.uploadFile(new File([''], '.gitkeep'), keepPath);
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

  async confirmDelete() {
    if (!this.pendingDelete) return;
    const path = this.pendingDelete;
    this.pendingDelete = null;
    document.getElementById('deleteModal').classList.remove('active');
    this.ui.showProgress('Deleting...');
    try {
      const isFolder = this.cachedFolders.some(f => f.path === path);
      if (isFolder) {
        await this.hf.deleteFolder(path);
      } else {
        await this.hf.deleteFile(path);
      }
      this.ui.showToast('Deleted successfully', 'success');
      this.fetchAndRender();
    } catch (err) {
      this.ui.showToast(err.message || 'Delete failed', 'error');
    } finally {
      this.ui.hideProgress();
    }
  }

  openPreview(file) {
    this.state.addToRecent(file);
    const url = getFileUrl(this.hf.apiBase, file.path);
    const modal = document.getElementById('previewModal');
    const body = document.getElementById('previewBody');
    const title = document.getElementById('previewFileName');

    title.textContent = file.name;
    body.innerHTML = '<div class="loading-state"><div class="spinner"></div></div>';
    modal.classList.add('active');

    // Download button
    document.getElementById('downloadFromPreview').onclick = () => this.downloadFile(url, file.name);

    if (isImage(file.name)) {
      body.innerHTML = `<img src="${url}" class="preview-image" alt="${file.name}">`;
    } else if (isPDF(file.name)) {
      body.innerHTML = `<iframe src="${url}" class="preview-iframe"></iframe>`;
    } else if (isText(file.name)) {
      fetch(url).then(r => r.text()).then(text => {
        body.innerHTML = `<pre class="preview-text">${this.escapeHtml(text)}</pre>`;
      }).catch(() => {
        body.innerHTML = '<div class="preview-fallback"><i class="ph-fill ph-file-x"></i><p>Could not load file preview</p></div>';
      });
    } else {
      body.innerHTML = `<div class="preview-fallback"><i class="ph-fill ph-file"></i><p>No preview available</p><a href="${url}" download="${file.name}" class="btn-primary" style="padding: 10px 24px; text-decoration: none; border-radius: 8px; margin-top: 12px;">Download</a></div>`;
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  downloadFile(url, name) {
    const a = document.createElement('a');
    a.href = url;
    a.download = name;
    a.target = '_blank';
    a.click();
  }
}

new App();
