const STARRED_KEY = 'docvault_starred';
const RECENT_KEY = 'docvault_recent';

class StateManager {
  constructor() {
    this.currentPath = [];
    this.searchQuery = '';
    this.viewMode = localStorage.getItem('view_mode') || 'grid'; // 'grid' | 'list'
    this.currentBrowse = 'files'; // 'files' | 'starred' | 'recent'
    this.isFetching = false;
    this.cachedFiles = [];
    this.starred = this.load(STARRED_KEY);
    this.recent = this.load(RECENT_KEY);
    this.listeners = [];
  }

  load(key) {
    try {
      return JSON.parse(localStorage.getItem(key)) || [];
    } catch {
      return [];
    }
  }

  save(key, data) {
    localStorage.setItem(key, JSON.stringify(data));
  }

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  notify(actionType = 'UPDATE', payload = null) {
    console.log(`[StateManager] ${actionType}`, payload || '');
    this.listeners.forEach(l => l(this));
  }

  setPath(path) {
    if (!Array.isArray(path)) return;
    this.currentPath = path;
    this.notify('SET_PATH', path);
  }

  setViewMode(mode) {
    if (!['grid', 'list'].includes(mode)) return;
    this.viewMode = mode;
    localStorage.setItem('view_mode', mode);
    this.notify('SET_VIEW_MODE', mode);
  }

  setSearchQuery(query) {
    this.searchQuery = typeof query === 'string' ? query : '';
    this.notify('SET_SEARCH', query);
  }

  setBrowseMode(mode) {
    if (!['files', 'starred', 'recent'].includes(mode)) return;
    this.currentBrowse = mode;
    this.notify('SET_BROWSE', mode);
  }

  toggleStar(path) {
    if (typeof path !== 'string') return;
    if (this.starred.includes(path)) {
      this.starred = this.starred.filter(p => p !== path);
    } else {
      this.starred.push(path);
    }
    this.save(STARRED_KEY, this.starred);
    this.notify('TOGGLE_STAR', path);
  }

  addToRecent(file) {
    if (!file || !file.path) return;
    this.recent = [file, ...this.recent.filter(f => f.path !== file.path)].slice(0, 20);
    this.save(RECENT_KEY, this.recent);
    this.notify('ADD_RECENT', file.path);
  }

  getFolderPath() {
    return this.currentPath.join('/');
  }
}

export const stateManager = new StateManager();
