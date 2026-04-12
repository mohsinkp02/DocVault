// DocVault — Offline-First Document Storage System
// Uses local Flask backend for all operations

const API_BASE = 'http://localhost:5000/api';
const USER_ID = 'default_user';
const DEFAULT_FOLDER = '';

const STARRED_KEY  = 'docvault_starred';
const RECENT_KEY   = 'docvault_recent';

// ─── API HELPERS ──────────────────────────────────────────
const API_HEADERS = {
  'X-User-ID': USER_ID,
  'Content-Type': 'application/json'
};

async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = { ...API_HEADERS, ...options.headers };
  return fetch(url, { ...options, headers });
}

// ─── FILE OPERATIONS ──────────────────────────────────────
async function listFilesAPI(path = DEFAULT_FOLDER) {
  try {
    const queryPath = path ? `?folder_path=${encodeURIComponent(path)}` : '';
    const res = await apiFetch(`/list${queryPath}`);
    
    if (!res.ok) {
      if (res.status === 404) return { files: [], folders: [] };
      throw new Error(`Failed to list files: ${res.status}`);
    }
    
    const data = await res.json();
    if (!data.success) {
      console.error('API error:', data.error);
      return { files: [], folders: [] };
    }
    
    const files = (data.files || []).map(f => ({
      path: f.path,
      name: f.name,
      size: f.size || 0,
      type: 'file',
      created_at: f.created_at,
      modified_at: f.modified_at
    }));
    
    const folders = (data.folders || []).map(f => ({
      path: f.path,
      name: f.name,
      type: 'folder',
      created_at: f.created_at,
      modified_at: f.modified_at
    }));

    return { files, folders };
  } catch (err) {
    console.error('List files error:', err);
    return { files: [], folders: [] };
  }
}

async function uploadFileAPI(file, destPath) {
  try {
    const folderPath = destPath || DEFAULT_FOLDER;
    const fileBlob = file instanceof File ? file : file.content;
    const filename = file instanceof File ? file.name : (file.name || 'upload.bin');
    
    const formData = new FormData();
    formData.append('folder_path', folderPath);
    formData.append('file', fileBlob, filename);
    
    const res = await fetch(`${API_BASE}/upload-file`, {
      method: 'POST',
      headers: { 'X-User-ID': USER_ID },
      body: formData
    });
    
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error || `Upload failed: ${res.status}`);
    }
    
    const data = await res.json();
    if (!data.success) throw new Error(data.error);
    
    return data;
  } catch (err) {
    console.error('Upload error:', err);
    throw err;
  }
}

async function deleteItemAPI(itemPath, itemType = 'file') {
  try {
    const endpoint = itemType === 'folder' ? '/delete-folder' : '/delete-file';
    const payload = itemType === 'folder'
      ? { folder_path: itemPath, force: true }
      : { file_path: itemPath };

    const res = await apiFetch(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Delete failed');
    }

    return true;
  } catch (err) {
    console.error('Delete error:', err);
    throw err;
  }
}

async function createFolderAPI(folderPath) {
  try {
    const res = await apiFetch('/create-folder', {
      method: 'POST',
      body: JSON.stringify({ folder_path: folderPath })
    });
    
    if (!res.ok) throw new Error(`Create folder failed: ${res.status}`);
    
    const data = await res.json();
    if (!data.success) throw new Error(data.error);
    
    return data;
  } catch (err) {
    console.error('Create folder error:', err);
    throw err;
  }
}

async function renameItemAPI(itemPath, newName) {
  try {
    const res = await apiFetch('/rename', {
      method: 'POST',
      body: JSON.stringify({ item_path: itemPath, new_name: newName })
    });
    
    if (!res.ok) throw new Error(`Rename failed: ${res.status}`);
    
    const data = await res.json();
    if (!data.success) throw new Error(data.error);
    
    return data;
  } catch (err) {
    console.error('Rename error:', err);
    throw err;
  }
}

async function getStorageStatsAPI() {
  try {
    const res = await apiFetch('/storage-stats');
    
    if (!res.ok) throw new Error(`Storage stats failed: ${res.status}`);
    
    const data = await res.json();
    if (!data.success) throw new Error(data.error);
    
    return data;
  } catch (err) {
    console.error('Storage stats error:', err);
    return { total_size: 0, total_files: 0, total_folders: 0 };
  }
}

// ─── STATE ────────────────────────────────────────────────
let currentPath     = [];
let searchQuery     = '';
let currentViewMode = 'grid';  // grid | list
let currentBrowse   = 'files'; // files | starred | recent
let isFetching      = false;
let pendingDeletePath = null;
let pendingDeleteType = 'file';
let cachedFiles     = [];      // flat list from last fetch
let lastFetchPath   = null;    // Track last fetched path to prevent duplicates
let lastFetchTime   = 0;       // Track when last fetch occurred

// ─── DOM REFS ─────────────────────────────────────────────
const $ = id => document.getElementById(id);

const newBtn           = $('newBtn'),      newDropdown      = $('newDropdown');
const createFolderBtn  = $('createFolderBtn');
const uploadFileBtn    = $('uploadFileBtn');
const createFolderModal= $('createFolderModal'), closeNameModal = $('closeNameModal');
const cancelFolderBtn  = $('cancelFolderBtn'),   confirmFolderBtn = $('confirmFolderBtn');
const folderNameInput  = $('folderNameInput');
const breadcrumbsEl    = $('breadcrumbs');
const foldersContainer = $('foldersContainer'), filesContainer = $('filesContainer');
const fileInput        = $('fileInput');
const uploadProgress   = $('uploadProgress'), progressText  = $('progressText');
const searchInput      = $('searchInput'), toastContainer   = $('toastContainer');
const deleteModal      = $('deleteModal'), closeDeleteModal  = $('closeDeleteModal');
const cancelDeleteBtn  = $('cancelDeleteBtn'), confirmDeleteBtn = $('confirmDeleteBtn');
const navMyFiles       = $('navMyFiles'), navRecent         = $('navRecent'), navStarred = $('navStarred');
const viewGrid         = $('viewGrid'),   viewList           = $('viewList');
const previewModal     = $('previewModal'), closePreviewModal = $('closePreviewModal');
const previewBody      = $('previewBody'), previewFileName   = $('previewFileName');
const downloadFromPreview = $('downloadFromPreview');
const storageProgress  = $('storageProgress'), storageUsageText = $('storageUsageText');
const contentArea      = document.querySelector('.content-area');


// ─── TOAST ────────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const icons = {
    success: 'ph-fill ph-check-circle',
    error:   'ph-fill ph-warning-circle',
    info:    'ph-fill ph-info',
    warning: 'ph-fill ph-warning'
  };
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = `<i class="${icons[type] || icons.info}"></i><span>${msg}</span>`;
  toastContainer.appendChild(t);
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, 3500);
}

// ─── HELPERS ──────────────────────────────────────────────
function getFolderPath() {
  if (currentPath.length === 0) return DEFAULT_FOLDER;
  const prefix = DEFAULT_FOLDER ? `${DEFAULT_FOLDER}/` : '';
  return `${prefix}${currentPath.join('/')}`;
}
function getFilePath(name) {
  const folderPath = getFolderPath();
  return folderPath ? `${folderPath}/${name}` : name;
}
function formatSize(bytes) {
  if (!bytes || bytes === 0) return '—';
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB';
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
  if (bytes >= 1024) return Math.round(bytes / 1024) + ' KB';
  return bytes + ' B';
}
function getExt(name) { return (name.split('.').pop() || '').toLowerCase(); }
function getFileIcon(name) {
  const n = name.toLowerCase();
  if (n.endsWith('.pdf'))                         return { icon: 'ph-fill ph-file-pdf',     color: '#f85149' };
  if (n.match(/\.docx?$/))                        return { icon: 'ph-fill ph-file-text',    color: '#4299e1' };
  if (n.match(/\.xlsx?$/))                        return { icon: 'ph-fill ph-file-text',    color: '#38a169' };
  if (n.match(/\.pptx?$/))                        return { icon: 'ph-fill ph-presentation',color: '#e07b39' };
  if (n.match(/\.(jpg|jpeg|png|gif|webp|svg)$/))  return { icon: 'ph-fill ph-image',        color: '#9f7aea' };
  if (n.match(/\.(mp4|mov|avi|mkv|webm)$/))       return { icon: 'ph-fill ph-video',        color: '#fc8181' };
  if (n.match(/\.(mp3|wav|aac|flac|ogg)$/))       return { icon: 'ph-fill ph-music-notes',  color: '#68d391' };
  if (n.match(/\.(zip|rar|7z|tar|gz)$/))          return { icon: 'ph-fill ph-file-archive', color: '#f6e05e' };
  if (n.match(/\.(js|py|ts|html|css|json|xml|sh|java|cpp|c)$/)) return { icon: 'ph-fill ph-file-code', color: '#63b3ed' };
  if (n.match(/\.(txt|md|csv|log)$/))             return { icon: 'ph-fill ph-file-text',    color: '#a0aec0' };
  return { icon: 'ph-fill ph-file', color: '#79c0ff' };
}
function isImage(name) { return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(name); }
function isPDF(name)   { return /\.pdf$/i.test(name); }
function isText(name)  { return /\.(txt|md|csv|log|json|xml|html|css|js|ts|py|sh|java|yaml|yml)$/i.test(name); }

function getFileEmoji(ext) {
  const extLower = ext.toLowerCase();
  if (['pdf'].includes(extLower)) return '📄';
  if (['doc', 'docx'].includes(extLower)) return '📝';
  if (['xls', 'xlsx'].includes(extLower)) return '📊';
  if (['ppt', 'pptx'].includes(extLower)) return '📽️';
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(extLower)) return '🖼️';
  if (['mp4', 'mov', 'avi', 'mkv', 'webm'].includes(extLower)) return '🎥';
  if (['mp3', 'wav', 'aac', 'flac', 'ogg'].includes(extLower)) return '🎵';
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(extLower)) return '📦';
  if (['js', 'ts', 'py', 'java', 'cpp', 'c', 'html', 'css'].includes(extLower)) return '💻';
  if (['txt', 'md', 'csv', 'log', 'json', 'xml', 'yaml', 'yml'].includes(extLower)) return '📄';
  return '📄';
}

function formatDate(timestamp) {
  if (!timestamp) return 'Recently';
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
}

function getFileUrl(filePath) {
  // Download from local Flask backend
  const encodedPath = String(filePath)
    .split('/')
    .map(segment => encodeURIComponent(segment))
    .join('/');
  return `${API_BASE}/download/${encodedPath}`;
}

// ─── PERSISTENCE ──────────────────────────────────────────
function getStarred() { try { return JSON.parse(localStorage.getItem(STARRED_KEY)) || []; } catch { return []; } }
function isStarred(path) { return getStarred().includes(path); }
function toggleStar(path) {
  let s = getStarred();
  if (s.includes(path)) s = s.filter(x => x !== path);
  else s.push(path);
  localStorage.setItem(STARRED_KEY, JSON.stringify(s));
  renderView();
}
function getRecent() { try { return JSON.parse(localStorage.getItem(RECENT_KEY)) || []; } catch { return []; } }
function addToRecent(path, name, type) {
  let r = getRecent();
  r = [{ path, name, type }, ...r.filter(x => x.path !== path)].slice(0, 10);
  localStorage.setItem(RECENT_KEY, JSON.stringify(r));
}

// ─── STORAGE STATS ────────────────────────────────────────
async function updateStorageStats() {
  try {
    const stats = await getStorageStatsAPI();
    const totalBytes = stats.total_size || 0;
    const count      = stats.total_files || 0;
    const MAX_BYTES  = 10 * 1024 * 1024 * 1024; // 10 GB cap display
    const pct        = Math.min((totalBytes / MAX_BYTES) * 100, 100).toFixed(1);
    if (storageProgress)   storageProgress.style.width = pct + '%';
    if (storageUsageText)  storageUsageText.textContent = `${count} file${count !== 1 ? 's' : ''} • ${formatSize(totalBytes)} used`;
  } catch (err) {
    console.error('Failed to update storage stats:', err);
  }
}

// ─── SKELETON LOADING ─────────────────────────────────────
function showSkeletons(container, count = 6) {
  container.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const el = document.createElement('div');
    el.className = 'skeleton skeleton-card';
    el.innerHTML = `
      <div class="skeleton-icon"></div>
      <div class="skeleton-info">
        <div class="skeleton-name"></div>
        <div class="skeleton-meta"></div>
      </div>
    `;
    container.appendChild(el);
  }
}

// ─── FETCH FILES ──────────────────────────────────────────
async function fetchAndRender() {
  if (isFetching) {
    return;
  }
  isFetching = true;
  const container = currentViewMode === 'grid' ? 'grid-container' : 'list-container';
  foldersContainer.className = container;
  filesContainer.className   = container;
  showSkeletons(foldersContainer, 3);
  showSkeletons(filesContainer,   6);
  try {
    const prefix   = getFolderPath();
    const pathSnapshot = JSON.stringify(currentPath); // Capture for safety check
    const { files, folders } = await listFilesAPI(prefix);
    
    // SAFETY CHECK: Path may have changed due to user clicking elsewhere
    if (JSON.stringify(currentPath) !== pathSnapshot) {
      return;
    }
    
    // Update storage stats from API
    await updateStorageStats();

    // Apply search filter
    let displayFiles = files;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      displayFiles = files.filter(f => f.path.toLowerCase().includes(q));
    }

    renderBreadcrumbs();
    renderFolders(folders);
    renderFiles(displayFiles);
  } catch (err) {
    console.error('Fetch error', err);
    showError(filesContainer, err.message);
    renderBreadcrumbs();
  } finally {
    isFetching = false;
  }
}

// Recursively get all files for storage calculation (not needed with backend stats)
async function getRecursiveFiles(path = '') {
  const { files, folders } = await listFilesAPI(path);
  let allFiles = [...files];
  
  for (const folder of folders) {
    const subPath = path ? `${path}/${folder.name}` : folder.name;
    const subFiles = await getRecursiveFiles(subPath);
    allFiles = allFiles.concat(subFiles);
  }
  
  return allFiles;
}

function showEmpty(container, hint = '') {
  container.innerHTML = `<div class="empty-state">
    <i class="ph-fill ph-folder-open"></i>
    <h3>Nothing here yet</h3>
    <p>${hint || 'Upload files or create folders to get started.'}</p>
  </div>`;
}
function showError(container, msg) {
  container.innerHTML = `<div class="empty-state">
    <i class="ph-fill ph-warning-circle" style="color:#ef4444"></i>
    <h3>Something went wrong</h3>
    <p style="color:#ef4444">${msg}</p>
  </div>`;
}

// ─── RENDER: BREADCRUMBS ──────────────────────────────────
function renderBreadcrumbs() {
  breadcrumbsEl.innerHTML = '';
  const root = document.createElement('span');
  root.className = 'breadcrumb-item' + (currentPath.length === 0 ? ' active' : '');
  root.textContent = 'My Files';
  root.style.cursor = 'pointer';
  root.addEventListener('click', (e) => { 
    e.stopPropagation();
    console.log('Breadcrumb root clicked'); // Debug
    currentPath = []; 
    fetchAndRender(); 
  });
  breadcrumbsEl.appendChild(root);
  
  currentPath.forEach((seg, idx) => {
    const sep = document.createElement('span');
    sep.className   = 'breadcrumb-separator';
    sep.innerHTML = '<i class="ph-bold ph-caret-right" style="font-size: 14px; margin: 0 4px"></i>';
    breadcrumbsEl.appendChild(sep);
    const crumb = document.createElement('span');
    crumb.className = 'breadcrumb-item' + (idx === currentPath.length - 1 ? ' active' : '');
    crumb.textContent = seg;
    crumb.style.cursor = 'pointer';
    crumb.addEventListener('click', (e) => { 
      e.stopPropagation();
      console.log('Breadcrumb', seg, 'clicked at index', idx); // Debug
      currentPath = currentPath.slice(0, idx + 1); 
      fetchAndRender(); 
    });
    breadcrumbsEl.appendChild(crumb);
  });
}

// ─── RENDER: FOLDERS ──────────────────────────────────────
function renderFolders(folders) {
  if (!folders.length) { foldersContainer.innerHTML = ''; return; }
  foldersContainer.innerHTML = '';
  folders.forEach((folder, index) => {
    const name = folder.path.split('/').pop();
    const card = document.createElement('div');
    card.className = 'folder-card';
    card.style.animationDelay = `${index * 50}ms`; // Staggered animation

    // Get folder metadata (placeholder - you can enhance this)
    const itemCount = Math.floor(Math.random() * 10) + 1; // Placeholder - replace with actual count
    const lastModified = 'Recently'; // Placeholder - replace with actual date

    card.innerHTML = `
      <div class="folder-icon-container">
        <svg class="folder-icon" width="56" height="56" viewBox="0 0 24 24" fill="none">
          <path d="M2 6.75C2 5.784 2.784 5 3.75 5H9.5l1.5 2H20.25C21.216 7 22 7.784 22 8.75v9.5A1.75 1.75 0 0 1 20.25 20H3.75A1.75 1.75 0 0 1 2 18.25z" fill="var(--folder-color)" opacity="0.3"/>
          <path d="M2 8.75C2 7.784 2.784 7 3.75 7H20.25C21.216 7 22 7.784 22 8.75v9.5A1.75 1.75 0 0 1 20.25 20H3.75A1.75 1.75 0 0 1 2 18.25z" fill="var(--folder-color)"/>
        </svg>
      </div>
      <div class="folder-info">
        <div class="folder-name" title="${name}">${name}</div>
        <div class="folder-meta">${itemCount} items • ${lastModified}</div>
      </div>
      <div class="folder-actions">
        <button class="action-btn" title="More options" aria-label="Folder options">
          <i class="ph-bold ph-dots-three-vertical"></i>
        </button>
        <div class="dropdown-menu">
          <button class="dropdown-item" data-action="share-folder" data-path="${folder.path}">
            <i class="ph-fill ph-share-network"></i> Share
          </button>
          <button class="dropdown-item danger" data-action="delete-folder" data-path="${folder.path}">
            <i class="ph-fill ph-trash"></i> Delete
          </button>
        </div>
      </div>`;

    // NAVIGATION HANDLER - Use a self-contained function to avoid closure issues
    const handleFolderClick = (e) => {
      // Don't navigate if clicking on the actions menu
      if (e.target.closest('.folder-actions')) {
        return;
      }

      // Stop all propagation for actual navigation clicks
      e.preventDefault();
      e.stopPropagation();
      e.stopImmediatePropagation();
      
      // Navigate into the folder
      currentPath.push(name);
      addToRecent(folder.path, name, 'folder');
      fetchAndRender();
      return false;
    };
    
    card.addEventListener('click', handleFolderClick, true); // Use capture phase

    // Attach menu functionality
    attachCardMenu(card, folder.path, 'folder');

    foldersContainer.appendChild(card);
  });
}

// ─── RENDER: FILES ────────────────────────────────────────
function renderFiles(files) {
  if (!files.length) { showEmpty(filesContainer); return; }
  filesContainer.innerHTML = '';
  files.forEach(file => {
    const name   = file.path.split('/').pop();
    const { icon, color } = getFileIcon(name);
    const ext    = getExt(name).toUpperCase() || 'FILE';
    const size   = formatSize(file.size);
    const url    = getFileUrl(file.path);
    const starred = isStarred(file.path);
    const card   = document.createElement('div');
    card.className = 'file-card';
    
    // Determine file type color
    let typeColor = '#64748b'; // default gray
    const extUpper = ext.toUpperCase();
    if (['PDF'].includes(extUpper)) typeColor = '#dc2626'; // red
    else if (['JPG', 'JPEG', 'PNG', 'GIF', 'WEBP', 'SVG', 'BMP', 'ICO'].includes(extUpper)) typeColor = '#7c3aed'; // purple  
    else if (['JS', 'TS', 'HTML', 'CSS', 'PY', 'JAVA', 'CPP', 'C', 'PHP', 'RB', 'GO', 'RS'].includes(extUpper)) typeColor = '#ca8a04'; // yellow
    else if (['DOC', 'DOCX', 'TXT', 'MD', 'RTF'].includes(extUpper)) typeColor = '#2563eb'; // blue
    else if (['XLS', 'XLSX', 'CSV'].includes(extUpper)) typeColor = '#16a34a'; // green
    else if (['PPT', 'PPTX'].includes(extUpper)) typeColor = '#dc2626'; // red
    else if (['ZIP', 'RAR', '7Z', 'TAR', 'GZ'].includes(extUpper)) typeColor = '#7c2d12'; // orange
    
    const isImg = isImage(name);
    const previewHTML = isImg 
      ? `<img src="${url}" alt="${name}" loading="lazy" onerror="this.parentElement.innerHTML='<span class=\\'file-icon\\'>📄</span>'">`
      : `<span class="file-icon">${getFileEmoji(ext)}</span>`;
    
    card.innerHTML = `
      <div class="file-preview">
        ${previewHTML}
      </div>
      <div class="file-info">
        <span class="file-type" style="background-color: ${typeColor}20; color: ${typeColor}">${ext}</span>
        <h4 class="file-name" title="${name}">${name}</h4>
        <p class="file-meta">${size} • ${file.modified_at ? formatDate(file.modified_at) : 'Recently'}</p>
      </div>
      <div class="file-actions">⋮</div>
      <div class="quick-actions">
        <button class="quick-btn" data-action="preview" title="Preview"><i class="ph-fill ph-eye"></i></button>
        <button class="quick-btn" data-action="download" title="Download"><i class="ph-fill ph-download-simple"></i></button>
      </div>`;
    
    card.addEventListener('click', (e) => {
      if (e.target.closest('.file-actions') || e.target.closest('.quick-actions')) return;
      openPreview(file.path, name, url);
    });
    
    // File actions menu
    const actionsBtn = card.querySelector('.file-actions');
    actionsBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      // Create dropdown menu
      const existingMenu = document.querySelector('.file-menu-dropdown');
      if (existingMenu) existingMenu.remove();
      
      const menu = document.createElement('div');
      menu.className = 'file-menu-dropdown';
      menu.innerHTML = `
        <button class="menu-item" data-action="preview">
          <i class="ph-fill ph-eye"></i> Open
        </button>
        <button class="menu-item" data-action="download">
          <i class="ph-fill ph-download-simple"></i> Download
        </button>
        <button class="menu-item" data-action="share">
          <i class="ph-fill ph-share-network"></i> Share
        </button>
        <button class="menu-item" data-action="star">
          <i class="ph-fill ph-star${starred ? '' : '-bold'}"></i> ${starred ? 'Unstar' : 'Star'}
        </button>
        <button class="menu-item" data-action="rename">
          <i class="ph-fill ph-pencil-simple"></i> Rename
        </button>
        <div class="menu-divider"></div>
        <button class="menu-item danger" data-action="delete">
          <i class="ph-fill ph-trash"></i> Delete
        </button>
      `;
      document.body.appendChild(menu);
      
      // Position menu after it's rendered
      requestAnimationFrame(() => {
        const rect = actionsBtn.getBoundingClientRect();
        const menuRect = menu.getBoundingClientRect();
        let top = rect.bottom + 8;
        let left = rect.right - menuRect.width;
        
        // Adjust if menu goes off-screen
        if (left < 8) left = 8;
        if (top + menuRect.height > window.innerHeight) {
          top = rect.top - menuRect.height - 8;
        }
        
        menu.style.top = `${top}px`;
        menu.style.left = `${left}px`;
      });
      
      // Handle menu clicks
      const handleMenuClick = (e) => {
        const btn = e.target.closest('.menu-item');
        if (!btn) return;
        const action = btn.dataset.action;
        menu.remove();
        document.removeEventListener('click', closeMenu);
        
        if (action === 'preview') openPreview(file.path, name, url);
        else if (action === 'download') downloadFile(url, name);
        else if (action === 'share') copyLink(url);
        else if (action === 'star') toggleStar(file.path);
        else if (action === 'rename') openRenameModal(file.path, name);
        else if (action === 'delete') openDeleteModal(file.path, name, 'file');
      };
      
      const closeMenu = (e) => {
        if (!menu.contains(e.target) && e.target !== actionsBtn) {
          menu.remove();
          document.removeEventListener('click', closeMenu);
        }
      };
      
      menu.addEventListener('click', handleMenuClick);
      document.addEventListener('click', closeMenu);
    });
    
    // Quick actions
    const quickActions = card.querySelector('.quick-actions');
    quickActions.addEventListener('click', (e) => {
      const btn = e.target.closest('.quick-btn');
      if (!btn) return;
      const action = btn.dataset.action;
      if (action === 'preview') openPreview(file.path, name, url);
      else if (action === 'download') downloadFile(url, name);
    });
    
    filesContainer.appendChild(card);
  });
}

// ─── CARD DROPDOWN MENUS ─────────────────────────────────
function attachCardMenu(card, path, type, meta = {}) {
  const menuBtn  = card.querySelector('.action-btn');
  const dropdown = card.querySelector('.dropdown-menu');
  if (!menuBtn || !dropdown) return;

  menuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    document.querySelectorAll('.dropdown-menu.open').forEach(d => { if (d !== dropdown) d.classList.remove('open'); });
    dropdown.classList.toggle('open');
  });

  dropdown.addEventListener('click', (e) => {
    e.stopPropagation();
    const btn    = e.target.closest('[data-action]');
    if (!btn) return;
    const action = btn.dataset.action;
    dropdown.classList.remove('open');

    if (action === 'preview')        openPreview(btn.dataset.path, btn.dataset.name, getFileUrl(btn.dataset.path));
    else if (action === 'share')     copyLink(btn.dataset.url);
    else if (action === 'share-folder') copyLink(window.location.href + '#' + path);
    else if (action === 'download')  downloadFile(btn.dataset.url, btn.dataset.name);
    else if (action === 'star')      toggleStar(btn.dataset.path);
    else if (action === 'rename')    openRenameModal(btn.dataset.path, btn.dataset.name);
    else if (action === 'delete') openDeleteModal(btn.dataset.path, btn.dataset.name || path.split('/').pop(), 'file');
    else if (action === 'delete-folder') openDeleteModal(path, path.split('/').pop(), 'folder');
  });
}

// Close dropdowns on outside click (but don't interfere with folder navigation)
document.addEventListener('click', (e) => {
  // Skip if clicking on a folder card itself
  if (e.target.closest('.folder-card')) {
    return;
  }
  
  // Close dropdowns
  document.querySelectorAll('.dropdown-menu.open').forEach(d => d.classList.remove('open'));
  newDropdown.classList.remove('active');
}, false); // Use bubble phase so folder capture phase fires first


// ─── PREVIEW MODAL ────────────────────────────────────────
let currentPreviewUrl = '';
function openPreview(filePath, name, url) {
  currentPreviewUrl = url;
  addToRecent(filePath, name, 'file');
  previewFileName.textContent = name;
  previewBody.innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Loading preview…</p></div>`;
  previewModal.classList.add('active');

  if (isImage(name)) {
    const img = new Image();
    img.src = url;
    img.className = 'preview-image';
    img.onload  = () => { previewBody.innerHTML = ''; previewBody.appendChild(img); };
    img.onerror = () => { previewBody.innerHTML = previewFallback(name, url, 'Image failed to load.'); };
  } else if (isPDF(name)) {
    previewBody.innerHTML = `<iframe class="preview-iframe" src="${url}" title="${name}"></iframe>`;
  } else if (isText(name)) {
    fetch(url)
      .then(r => r.ok ? r.text() : Promise.reject(r.status))
      .then(text => {
        const pre = document.createElement('pre');
        pre.className = 'preview-text';
        pre.textContent = text;
        previewBody.innerHTML = '';
        previewBody.appendChild(pre);
      })
      .catch(() => { previewBody.innerHTML = previewFallback(name, url, 'Could not load text.'); });
  } else {
    previewBody.innerHTML = previewFallback(name, url, 'No preview available for this file type.');
  }
}

function previewFallback(name, url, msg) {
  const { icon, color } = getFileIcon(name);
  return `<div class="preview-fallback">
    <i class="${icon}" style="color:${color}"></i>
    <p>${msg}</p>
    <a href="${url}" target="_blank" class="btn-primary" style="text-decoration:none;display:inline-flex;align-items:center;gap:8px;margin-top:16px">
      <i class="ph-fill ph-download-simple"></i> Download File
    </a>
  </div>`;
}

closePreviewModal.addEventListener('click', () => previewModal.classList.remove('active'));
previewModal.addEventListener('click', (e) => { if (e.target === previewModal) previewModal.classList.remove('active'); });
downloadFromPreview.addEventListener('click', () => { if (currentPreviewUrl) downloadFile(currentPreviewUrl, previewFileName.textContent); });

// ─── SHARE / DOWNLOAD ────────────────────────────────────
function copyLink(url) {
  navigator.clipboard.writeText(url)
    .then(() => showToast('🔗 Link copied to clipboard!', 'success'))
    .catch(() => { prompt('Copy this link:', url); });
}
function downloadFile(url, name) {
  const a = document.createElement('a');
  a.href = url; a.download = name; a.target = '_blank';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// ─── DELETE ───────────────────────────────────────────────
function openDeleteModal(path, name, type = 'file') {
  pendingDeletePath = path;
  pendingDeleteType = type;
  const p = deleteModal.querySelector('p');
  if (p) p.innerHTML = `This will permanently delete <strong>${name}</strong> from your repository.`;
  deleteModal.classList.add('active');
}
closeDeleteModal.addEventListener('click',  () => deleteModal.classList.remove('active'));
cancelDeleteBtn.addEventListener('click',   () => deleteModal.classList.remove('active'));
confirmDeleteBtn.addEventListener('click',  async () => {
  if (!pendingDeletePath) return;
  deleteModal.classList.remove('active');
  showProgress(`Deleting…`);
  try {
    await deleteItemAPI(pendingDeletePath, pendingDeleteType);
    showToast('✅ Deleted successfully.', 'success');
    fetchAndRender();
  } catch (err) {
    showToast('❌ Delete failed: ' + err.message, 'error');
  } finally {
    hideProgress();
    pendingDeletePath = null;
    pendingDeleteType = 'file';
  }
});

// ─── UPLOAD ───────────────────────────────────────────────
async function uploadFiles(fileList) {
  if (!fileList || !fileList.length) return;

  const files = Array.from(fileList);
  let done = 0;
  for (const file of files) {
    const destPath = getFolderPath();
    const filePath = getFilePath(file.name);
    showProgress(`Uploading ${file.name} (${done + 1}/${files.length})…`);
    try {
      await uploadFileAPI(file, destPath);
      addToRecent(filePath, file.name, 'file');
      done++;
    } catch (err) {
      showToast(`❌ Failed to upload ${file.name}: ${err.message}`, 'error');
    }
  }
  hideProgress();
  if (done > 0) {
    showToast(`✅ Uploaded ${done} file${done > 1 ? 's' : ''} successfully!`, 'success');
    fetchAndRender();
  }
}

// ─── DRAG & DROP ──────────────────────────────────────────
let dragCounter = 0;
contentArea.addEventListener('dragenter', (e) => {
  e.preventDefault(); dragCounter++;
  contentArea.classList.add('drag-over');
});
contentArea.addEventListener('dragleave', (e) => {
  e.preventDefault(); dragCounter--;
  if (dragCounter <= 0) { dragCounter = 0; contentArea.classList.remove('drag-over'); }
});
contentArea.addEventListener('dragover', (e) => { e.preventDefault(); });
contentArea.addEventListener('drop', (e) => {
  e.preventDefault(); dragCounter = 0;
  contentArea.classList.remove('drag-over');
  const files = e.dataTransfer?.files;
  if (files && files.length) uploadFiles(files);
});

// Also add drop to entire body for full-window drop
document.addEventListener('dragover', (e) => e.preventDefault());

// ─── PROGRESS BAR ────────────────────────────────────────
function showProgress(msg = 'Working…') {
  progressText.textContent = msg;
  uploadProgress.classList.add('active');
}
function hideProgress() { uploadProgress.classList.remove('active'); }

// ─── FILE INPUT ───────────────────────────────────────────
fileInput.addEventListener('change', () => {
  uploadFiles(fileInput.files);
  fileInput.value = '';
});



// ─── NEW BUTTON ───────────────────────────────────────────
newBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  newDropdown.classList.toggle('active');
});
createFolderBtn.addEventListener('click', () => {
  newDropdown.classList.remove('active');
  folderNameInput.value = '';
  createFolderModal.classList.add('active');
  setTimeout(() => folderNameInput.focus(), 100);
});
uploadFileBtn.addEventListener('click', () => {
  newDropdown.classList.remove('active');
  fileInput.click();
});

// ─── CREATE FOLDER ────────────────────────────────────────
closeNameModal.addEventListener('click',   () => createFolderModal.classList.remove('active'));
cancelFolderBtn.addEventListener('click',  () => createFolderModal.classList.remove('active'));
confirmFolderBtn.addEventListener('click', async () => {
  const name = folderNameInput.value.trim();
  if (!name) { folderNameInput.focus(); return; }
  createFolderModal.classList.remove('active');
  showProgress(`Creating folder "${name}"…`);
  try {
    const folderPath = getFilePath(name);
    await createFolderAPI(folderPath);
    showToast(`📁 Folder "${name}" created!`, 'success');
    fetchAndRender();
  } catch (err) {
    console.error('Folder creation failed:', err.message);
    showToast(`❌ Folder creation failed: ${err.message}`, 'error');
  } finally { hideProgress(); }
});
folderNameInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') confirmFolderBtn.click(); });

// ─── SEARCH ───────────────────────────────────────────────
let searchDebounce;
searchInput.addEventListener('input', () => {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => {
    searchQuery = searchInput.value.trim();
    fetchAndRender();
  }, 400);
});



// ─── NAV ──────────────────────────────────────────────────
function setNavActive(nav) {
  [navMyFiles, navRecent, navStarred].forEach(n => n.classList.remove('active'));
  nav.classList.add('active');
}

navMyFiles.addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();
  e.stopImmediatePropagation();
  currentBrowse = 'files'; currentPath = [];
  setNavActive(navMyFiles);
  fetchAndRender();
});

navRecent.addEventListener('click', (e) => {
  e.preventDefault();
  currentBrowse = 'recent';
  setNavActive(navRecent);
  renderRecentView();
});

navStarred.addEventListener('click', (e) => {
  e.preventDefault();
  currentBrowse = 'starred';
  setNavActive(navStarred);
  renderStarredView();
});

function renderRecentView() {
  foldersContainer.innerHTML = '';
  breadcrumbsEl.innerHTML    = '<span class="breadcrumb-item active">Recent</span>';
  const items = getRecent();
  filesContainer.innerHTML = '';
  if (!items.length) { showEmpty(filesContainer, 'No recently opened files.'); return; }
  items.forEach(item => {
    const { icon, color } = getFileIcon(item.name);
    const url = getFileUrl(item.path);
    const card = document.createElement('div');
    card.className = 'file-card';
    const ext = getExt(item.name).toUpperCase() || 'FILE';
    const isImg = isImage(item.name);
    const previewHTML = isImg 
      ? `<img src="${url}" alt="${item.name}" loading="lazy" onerror="this.parentElement.innerHTML='<span class=\\'file-icon\\'>📄</span>'">`
      : `<span class="file-icon">${getFileEmoji(ext)}</span>`;
    
    card.innerHTML = `
      <div class="file-preview">
        ${previewHTML}
      </div>
      <div class="file-info">
        <span class="file-type">${ext}</span>
        <h4 class="file-name" title="${item.name}">${item.name}</h4>
        <p class="file-meta">${item.path}</p>
      </div>
      <div class="file-actions">⋮</div>`;
    card.addEventListener('click', () => openPreview(item.path, item.name, url));
    filesContainer.appendChild(card);
  });
}

function renderStarredView() {
  foldersContainer.innerHTML = '';
  breadcrumbsEl.innerHTML    = '<span class="breadcrumb-item active">Starred</span>';
  const starred = getStarred();
  filesContainer.innerHTML = '';
  if (!starred.length) { showEmpty(filesContainer, 'No starred files yet.'); return; }
  starred.forEach(path => {
    const name = path.split('/').pop();
    const url  = getFileUrl(path);
    const { icon, color } = getFileIcon(name);
    const card = document.createElement('div');
    card.className = 'file-card';
    const ext = getExt(name).toUpperCase() || 'FILE';
    const isImg = isImage(name);
    const previewHTML = isImg 
      ? `<img src="${url}" alt="${name}" loading="lazy" onerror="this.parentElement.innerHTML='<span class=\\'file-icon\\'>📄</span>'">`
      : `<span class="file-icon">${getFileEmoji(ext)}</span>`;
    
    card.innerHTML = `
      <div class="file-preview">
        ${previewHTML}
      </div>
      <div class="file-info">
        <span class="file-type">${ext}</span>
        <h4 class="file-name" title="${name}">${name}</h4>
        <p class="file-meta">${path}</p>
      </div>
      <div class="file-actions">⋮</div>`;
    card.addEventListener('click', () => openPreview(path, name, url));
    filesContainer.appendChild(card);
  });
}

// ─── VIEW TOGGLES ─────────────────────────────────────────
viewGrid.addEventListener('click', () => {
  if (currentViewMode === 'grid') return;
  currentViewMode = 'grid';
  viewGrid.classList.add('active'); viewList.classList.remove('active');
  renderView();
});
viewList.addEventListener('click', () => {
  if (currentViewMode === 'list') return;
  currentViewMode = 'list';
  viewList.classList.add('active'); viewGrid.classList.remove('active');
  renderView();
});
function renderView() {
  if (currentBrowse === 'recent')  { renderRecentView(); return; }
  if (currentBrowse === 'starred') { renderStarredView(); return; }
  fetchAndRender();
}

// ─── KEYBOARD SHORTCUTS ───────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    previewModal.classList.remove('active');
    deleteModal.classList.remove('active');
    createFolderModal.classList.remove('active');
  }
});

// ─── RENAME ───────────────────────────────────────────────
const renameModal       = $('renameModal');
const closeRenameModal  = $('closeRenameModal');
const cancelRenameBtn   = $('cancelRenameBtn');
const confirmRenameBtn  = $('confirmRenameBtn');
const renameInput       = $('renameInput');
let pendingRenamePath   = null;

function openRenameModal(filePath, currentName) {
  pendingRenamePath      = filePath;
  renameInput.value      = currentName;
  renameModal.classList.add('active');
  setTimeout(() => { renameInput.select(); }, 100);
}

closeRenameModal.addEventListener('click',  () => renameModal.classList.remove('active'));
cancelRenameBtn.addEventListener('click',   () => renameModal.classList.remove('active'));
renameInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') confirmRenameBtn.click(); });

confirmRenameBtn.addEventListener('click', async () => {
  const newName = renameInput.value.trim();
  if (!newName || !pendingRenamePath) return;

  const oldPath  = pendingRenamePath;
  const dir      = oldPath.includes('/') ? oldPath.substring(0, oldPath.lastIndexOf('/')) : '';
  const newPath  = dir ? `${dir}/${newName}` : newName;

  if (oldPath === newPath) { renameModal.classList.remove('active'); return; }

  renameModal.classList.remove('active');
  showProgress(`Renaming to "${newName}"…`);
  try {
    // Use rename API for direct renaming
    await renameItemAPI(oldPath, newName);
    showToast(`✅ Renamed to "${newName}"!`, 'success');
    fetchAndRender();
  } catch (err) {
    showToast('❌ Rename failed: ' + err.message, 'error');
  } finally { hideProgress(); pendingRenamePath = null; }
});

// ─── INIT ─────────────────────────────────────────────────
// Initialize offline-first DocVault
(function initApp() {
  // Show welcome message
  showToast('🎉 Welcome to DocVault! Loading your files...', 'info');
  
  // Auto-load files from local backend
  fetchAndRender();
})();
