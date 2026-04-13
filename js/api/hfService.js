// Production-grade API Client with Proxy Support, TTL Caching, and Retries
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes


class HFService {
  constructor() {
    this.apiBase = '/api';
    this.cache = new Map();
    this.retryLimit = 3;
    this.retryDelay = 1000; // 1s start for exponential backoff

    // These are used by getFileUrl() in main.js for building download/preview URLs
    this.username = 'mohsin-devs';
    this.dataset = 'docvault-storage';


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
    const url = `${this.apiBase}/list${queryPath}`;
    
    // Add X-User-ID header to match app.py expected requests
    const res = await this.fetchWithRetry(url, { headers: { 'X-User-ID': 'default_user' } });
    const data = await res.json();

    const result = { files: [], folders: [] };

    if (data && data.success) {
      if (data.files) {
        for (const item of data.files) {
          if (!item.path.endsWith('/.gitkeep') && item.path !== '.gitkeep' && !item.path.endsWith('/gitkeep') && item.path !== 'gitkeep') {
            result.files.push({
              path: item.path,
              name: item.name,
              size: item.size || 0,
              type: 'file',
              lastModified: item.modified_at
            });
          }
        }
      }
      if (data.folders) {
        for (const item of data.folders) {
          result.folders.push({
            path: item.path,
            name: item.name,
            type: 'folder'
          });
        }
      }
    }

    this.cache.set(cacheKey, { data: result, timestamp: Date.now() });
    return result;
  }

  async uploadFile(file, destPath) {
    const formData = new FormData();
    const folderPath = destPath.includes('/') ? destPath.substring(0, destPath.lastIndexOf('/')) : '';
    const filename = file instanceof File ? file.name : destPath.split('/').pop();
    const fileBlob = file instanceof File ? file : new Blob([file.content || '']);
    
    formData.append('folder_path', folderPath);
    formData.append('file', fileBlob, filename);

    const url = `${this.apiBase}/upload-file`;

    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'X-User-ID': 'default_user' }, // Let browser set Content-Type with boundary
      body: formData
    });

    this.clearCache();
    return await res.json();
  }

  async deleteFile(path) {
    const url = `${this.apiBase}/delete-file`;
    await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': 'default_user' },
      body: JSON.stringify({ file_path: path }),
    });

    this.clearCache();
    return true;
  }

  async deleteFolder(folderPath) {
    const url = `${this.apiBase}/delete-folder`;
    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-ID': 'default_user' },
      body: JSON.stringify({ folder_path: folderPath, force: true }),
    });

    this.clearCache();
    return await res.json();
  }

  clearCache() {
    this.cache.clear();
  }
}

export const hfService = new HFService();
