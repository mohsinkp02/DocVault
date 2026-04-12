import { getFileIcon, getFileEmoji, getExt, isImage, formatSize, formatDate } from '../utils/formatters.js';

export class UIRenderer {
  constructor(stateManager, hfService) {
    this.state = stateManager;
    this.hf = hfService;
    this.containers = {
      folders: document.getElementById('foldersContainer'),
      files: document.getElementById('filesContainer'),
      breadcrumbs: document.getElementById('breadcrumbs'),
      toast: document.getElementById('toastContainer'),
      progress: document.getElementById('uploadProgress'),
      progressText: document.getElementById('progressText')
    };
  }

  showToast(msg, type = 'info') {
    const icons = {
      success: 'ph-fill ph-check-circle',
      error: 'ph-fill ph-warning-circle',
      info: 'ph-fill ph-info',
      warning: 'ph-fill ph-warning'
    };
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.innerHTML = `<i class="${icons[type] || icons.info}"></i><span>${msg}</span>`;
    this.containers.toast.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    setTimeout(() => {
      t.classList.remove('show');
      setTimeout(() => t.remove(), 400);
    }, 3500);
  }

  showProgress(msg = 'Working...') {
    this.containers.progressText.textContent = msg;
    this.containers.progress.classList.add('active');
  }

  hideProgress() {
    this.containers.progress.classList.remove('active');
  }

  renderBreadcrumbs(onCrumbClick) {
    this.containers.breadcrumbs.innerHTML = '';
    const root = document.createElement('span');
    root.className = 'breadcrumb-item' + (this.state.currentPath.length === 0 ? ' active' : '');
    root.textContent = 'My Files';
    root.onclick = () => onCrumbClick([]);
    this.containers.breadcrumbs.appendChild(root);

    this.state.currentPath.forEach((seg, idx) => {
      const sep = document.createElement('span');
      sep.className = 'breadcrumb-separator';
      sep.innerHTML = '<i class="ph-bold ph-caret-right" style="font-size: 14px; margin: 0 4px"></i>';
      this.containers.breadcrumbs.appendChild(sep);

      const crumb = document.createElement('span');
      crumb.className = 'breadcrumb-item' + (idx === this.state.currentPath.length - 1 ? ' active' : '');
      crumb.textContent = seg;
      crumb.onclick = () => onCrumbClick(this.state.currentPath.slice(0, idx + 1));
      this.containers.breadcrumbs.appendChild(crumb);
    });
  }

  renderFolders(folders, onFolderClick, onDelete) {
    this.containers.folders.innerHTML = '';
    if (!folders.length) return;

    folders.forEach(folder => {
      const card = document.createElement('div');
      card.className = 'folder-card';
      card.innerHTML = `
        <div class="card-top-row">
          <div class="item-icon">
            <svg class="folder-icon" width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path d="M2 6.75C2 5.784 2.784 5 3.75 5H9.5l1.5 2H20.25C21.216 7 22 7.784 22 8.75v9.5A1.75 1.75 0 0 1 20.25 20H3.75A1.75 1.75 0 0 1 2 18.25z" fill="var(--folder-color)" opacity="0.3"/>
              <path d="M2 8.75C2 7.784 2.784 7 3.75 7H20.25C21.216 7 22 7.784 22 8.75v9.5A1.75 1.75 0 0 1 20.25 20H3.75A1.75 1.75 0 0 1 2 18.25z" fill="var(--folder-color)"/>
            </svg>
          </div>
          <div class="card-menu">
            <button class="icon-btn card-menu-btn" title="More options"><i class="ph-bold ph-dots-three-vertical"></i></button>
            <div class="dropdown-menu">
              <button class="dropdown-item danger" data-action="delete">
                <i class="ph-fill ph-trash"></i> Delete
              </button>
            </div>
          </div>
        </div>
        <div class="item-name">${folder.name}</div>
        <div class="item-meta">Folder</div>`;

      card.onclick = (e) => {
        if (e.target.closest('.card-menu')) return;
        onFolderClick(folder.name);
      };

      card.querySelector('.dropdown-item').onclick = (e) => {
        e.stopPropagation();
        onDelete(folder.path, folder.name);
      };

      const menuBtn = card.querySelector('.card-menu-btn');
      const menu = card.querySelector('.dropdown-menu');
      menuBtn.onclick = (e) => {
        e.stopPropagation();
        menu.classList.toggle('open');
      };

      this.containers.folders.appendChild(card);
    });
  }

  renderFiles(files, actions) {
    this.containers.files.innerHTML = '';
    const mode = this.state.viewMode;
    this.containers.files.className = mode === 'grid' ? 'grid-container' : 'list-container';

    if (!files.length) {
      this.showEmpty();
      return;
    }

    files.forEach(file => {
      const card = document.createElement('div');
      card.className = mode === 'grid' ? 'file-card' : 'file-list-item';
      
      const { icon, color } = getFileIcon(file.name);
      const ext = getExt(file.name).toUpperCase();
      const size = formatSize(file.size);
      const starred = this.state.starred.includes(file.path);
      const url = actions.getUrl(file.path);

      if (mode === 'grid') {
        const isImg = isImage(file.name);
        const previewHTML = isImg
          ? `<img src="${url}" alt="${file.name}" loading="lazy" onerror="this.parentElement.innerHTML='<span class=\\'file-icon\\'>📄</span>'">`
          : `<span class="file-icon">${getFileEmoji(ext)}</span>`;

        card.innerHTML = `
          <div class="file-preview">${previewHTML}</div>
          <div class="file-info">
            <span class="file-type" style="background-color: ${color}20; color: ${color}">${ext}</span>
            <h4 class="file-name" title="${file.name}">${file.name}</h4>
            <p class="file-meta">${size} • ${file.lastModified ? formatDate(file.lastModified) : 'Recently'}</p>
          </div>
          <div class="file-actions">⋮</div>
          <div class="quick-actions">
            <button class="quick-btn" data-action="preview" title="Preview"><i class="ph-fill ph-eye"></i></button>
            <button class="quick-btn" data-action="download" title="Download"><i class="ph-fill ph-download-simple"></i></button>
          </div>`;
      } else {
        card.innerHTML = `
          <div class="list-icon" style="color: ${color}"><i class="${icon}"></i></div>
          <div class="list-info">
            <h4 class="list-name" title="${file.name}">${file.name}</h4>
            <span class="list-meta">${size} • ${ext}</span>
          </div>
          <div class="list-actions">
            <button class="icon-btn" data-action="star" title="${starred ? 'Unstar' : 'Star'}"><i class="ph-fill ph-star${starred ? '' : '-bold'}"></i></button>
            <button class="icon-btn" data-action="download" title="Download"><i class="ph-fill ph-download-simple"></i></button>
            <button class="icon-btn" data-action="delete" title="Delete"><i class="ph-fill ph-trash"></i></button>
          </div>`;
      }

      card.onclick = (e) => {
        if (e.target.closest('.file-actions, .quick-actions, .list-actions')) return;
        actions.onPreview(file);
      };

      // Action Handlers
      card.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;
        const action = btn.dataset.action;
        if (action === 'preview') actions.onPreview(file);
        else if (action === 'download') actions.onDownload(url, file.name);
        else if (action === 'star') actions.onStar(file.path);
        else if (action === 'delete') actions.onDelete(file.path, file.name);
      });

      this.containers.files.appendChild(card);
    });
  }

  showEmpty() {
    this.containers.files.innerHTML = `
      <div class="empty-state">
        <i class="ph-fill ph-folder-open"></i>
        <h3>Nothing here yet</h3>
        <p>Upload files or create folders to get started.</p>
      </div>`;
  }

  showSkeletons(foldersCount = 3, filesCount = 6) {
    this.containers.folders.innerHTML = '';
    this.containers.files.innerHTML = '';
    for (let i = 0; i < foldersCount; i++) {
      const el = document.createElement('div');
      el.className = 'skeleton skeleton-card';
      this.containers.folders.appendChild(el);
    }
    for (let i = 0; i < filesCount; i++) {
      const el = document.createElement('div');
      el.className = 'skeleton skeleton-card';
      this.containers.files.appendChild(el);
    }
  }
}
