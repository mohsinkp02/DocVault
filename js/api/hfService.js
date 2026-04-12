// Production-grade API Client with Proxy Support, TTL Caching, and Retries
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes


class HFService {
  constructor() {
    this.apiBase = 'http://localhost:5000/api';
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

  async listFiles(path = '', recursive = false) {
    const cacheKey = `list-${path}-${recursive}`;
    const cached = this.cache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp < CACHE_TTL)) {
      return cached.data;
    }

    const url = `${this.apiBase}/list?path=${encodeURIComponent(path)}&recursive=${recursive}`;
    const res = await this.fetchWithRetry(url);
    const data = await res.json();

    const result = { files: [], folders: [] };

    if (Array.isArray(data)) {
      for (const item of data) {
        if (item.type === 'file' && !item.path.endsWith('/.gitkeep') && item.path !== '.gitkeep') {
          result.files.push({
            path: item.path,
            name: item.path.split('/').pop(),
            size: item.size || 0,
            type: 'file',
            lastModified: item.lastModified
          });
        } else if (item.type === 'directory') {
          result.folders.push({
            path: item.path,
            name: item.path.split('/').pop(),
            type: 'directory'
          });
        }
      }
    }

    this.cache.set(cacheKey, { data: result, timestamp: Date.now() });
    return result;
  }

  async uploadFile(file, destPath) {
    const base64Content = await this.fileToBase64(file);
    const url = `${this.apiBase}/upload`;

    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: destPath,
        content: base64Content,
        summary: `Upload ${destPath.split('/').pop()}`
      }),
    });

    this.clearCache();
    return await res.json();
  }

  async deleteFile(path) {
    const url = `${this.apiBase}/delete`;
    await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });

    this.clearCache();
    return true;
  }

  async deleteFolder(folderPath) {
    const url = `${this.apiBase}/delete-folder`;
    const res = await this.fetchWithRetry(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: folderPath }),
    });

    this.clearCache();
    return await res.json();
  }

  async fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      const blob = file instanceof File ? file : file.content;
      reader.readAsDataURL(blob);
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = reject;
    });
  }

  clearCache() {
    this.cache.clear();
  }
}

export const hfService = new HFService();
