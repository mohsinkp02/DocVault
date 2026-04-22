// Enhanced HF Service with Versioning and Standardized Responses
const CACHE_TTL = 60 * 1000; // 60 seconds (aligned with backend HF cache)

class HFService {
  constructor() {
    this.apiBase = null;
    this.apiBasePromise = null;
    this.cache = new Map();
    this.retryLimit = 3;
    this.retryDelay = 1000;
  }

  getUserId() {
    return localStorage.getItem('docvault_user_id') || 'default_user';
  }

  async getApiBase() {
    if (this.apiBase) return this.apiBase;
    if (this.apiBasePromise) return this.apiBasePromise;

    this.apiBasePromise = (async () => {
      const configuredBase = window.__DOCVAULT_API_BASE__;
      if (configuredBase && typeof configuredBase === 'string') {
        this.apiBase = configuredBase.replace(/\/$/, '');
        return this.apiBase;
      }

      const { protocol, hostname, origin, port } = window.location;
      const host = hostname || '127.0.0.1';
      const candidates = [`${origin}/api`];

      if (port !== '5000') candidates.push(`${protocol}//${host}:5000/api`);
      if (port !== '7860') candidates.push(`${protocol}//${host}:7860/api`);

      for (const candidate of candidates) {
        try {
          const response = await fetch(`${candidate}/health`, {
            method: 'GET',
            headers: { 'X-User-ID': this.getUserId() }
          });

          if (response.ok) {
            this.apiBase = candidate;
            return candidate;
          }
        } catch (err) {
          // Try the next candidate quietly.
        }
      }

      this.apiBase = '/api';
      return this.apiBase;
    })();

    return this.apiBasePromise;
  }

  async fetchWithRetry(url, options = {}, retries = this.retryLimit) {
    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        if (response.status >= 500 && retries > 0) throw new Error('Server error');
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Request failed: ${response.status}`);
      }
      return response;
    } catch (err) {
      if (retries > 0) {
        const delay = this.retryDelay * Math.pow(2, this.retryLimit - retries);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.fetchWithRetry(url, options, retries - 1);
      }
      throw err;
    }
  }

  async listFiles(path = '') {
    const cacheKey = `list-${path}`;
    const cached = this.cache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp < CACHE_TTL)) {
      return cached.data;
    }

    const queryPath = path ? `?folder_path=${encodeURIComponent(path)}` : '';
    const apiBase = await this.getApiBase();
    const url = `${apiBase}/list${queryPath}`;
    
    const res = await this.fetchWithRetry(url, { headers: { 'X-User-ID': this.getUserId() } });
    const data = await res.json();

    const result = { files: [], folders: [] };

    // Validate response structure
    if (!data || typeof data !== 'object' || data.success !== true) {
      console.warn('Invalid API response structure:', data);
      this.cache.set(cacheKey, { data: result, timestamp: Date.now() });
      return result;
    }

    if (Array.isArray(data.files)) {
      for (const item of data.files) {
        result.files.push({
          path: item.path || '',
          name: item.name || 'unnamed',
          size: item.size || 0,
          type: 'file',
          lastModified: item.modified_at,
          storage: item.storage
        });
      }
    }
    
    if (Array.isArray(data.folders)) {
      for (const item of data.folders) {
        result.folders.push({
          path: item.path || '',
          name: item.name || 'unnamed',
          type: 'folder',
          storage: item.storage
        });
      }
    }

    this.cache.set(cacheKey, { data: result, timestamp: Date.now() });
    return result;
  }

  async uploadFile(file, destPath) {
    const formData = new FormData();
    // standardized folder path extraction
    const folderPath = destPath.includes('/') ? destPath.substring(0, destPath.lastIndexOf('/')) : '';
    const filename = file instanceof File ? file.name : destPath.split('/').pop();
    const fileBlob = file instanceof File ? file : new Blob([file.content || '']);
    
    formData.append('folder_path', folderPath);
    formData.append('file', fileBlob, filename);

    const apiBase = await this.getApiBase();
    const url = `${apiBase}/upload-file`;

    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'X-User-ID': this.getUserId() },
      body: formData
    });

    this.clearCache();
    return await res.json();
  }

  async createFolder(folderPath) {
    const apiBase = await this.getApiBase();
    const url = `${apiBase}/create-folder`;
    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': this.getUserId() },
      body: JSON.stringify({ folder_path: folderPath }),
    });

    this.clearCache();
    return await res.json();
  }

  async deleteFile(path) {
    const apiBase = await this.getApiBase();
    const url = `${apiBase}/delete-file`;
    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': this.getUserId() },
      body: JSON.stringify({ file_path: path }),
    });

    this.clearCache();
    const data = await res.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to delete file');
    }
    return data;
  }

  async deleteFolder(folderPath) {
    const apiBase = await this.getApiBase();
    const url = `${apiBase}/delete-folder`;
    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': this.getUserId() },
      body: JSON.stringify({ folder_path: folderPath }),
    });

    this.clearCache();
    const data = await res.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to delete folder');
    }
    return data;
  }

  async getHistory(path) {
    const apiBase = await this.getApiBase();
    const url = `${apiBase}/history?path=${encodeURIComponent(path)}`;
    const res = await this.fetchWithRetry(url, { headers: { 'X-User-ID': this.getUserId() } });
    const data = await res.json();
    
    if (!data || !data.success) {
      console.warn('Failed to get history:', data?.error || 'Unknown error');
      return [];
    }
    
    return Array.isArray(data.history) ? data.history : [];
  }

  async restoreVersion(path, revision, asCopy = false) {
    const apiBase = await this.getApiBase();
    const url = `${apiBase}/restore`;
    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': this.getUserId() },
      body: JSON.stringify({ path, revision, as_copy: asCopy }),
    });

    this.clearCache();
    return await res.json();
  }

  async renameItem(itemPath, newName) {
    const apiBase = await this.getApiBase();
    const url = `${apiBase}/rename`;
    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': this.getUserId() },
      body: JSON.stringify({ item_path: itemPath, new_name: newName }),
    });

    this.clearCache();
    return await res.json();
  }

  clearCache() {
    this.cache.clear();
  }
}

export const hfService = new HFService();
