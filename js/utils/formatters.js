export function formatSize(bytes) {
  if (!bytes || bytes === 0) return '—';
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB';
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
  if (bytes >= 1024) return Math.round(bytes / 1024) + ' KB';
  return bytes + ' B';
}

export function getExt(name) { return (name.split('.').pop() || '').toLowerCase(); }

export function getFileIcon(name) {
  const n = name.toLowerCase();
  if (n.endsWith('.pdf')) return { icon: 'ph-fill ph-file-pdf', color: '#dc2626' };
  if (n.match(/\.docx?$/)) return { icon: 'ph-fill ph-file-text', color: '#2563eb' };
  if (n.match(/\.xlsx?$/)) return { icon: 'ph-fill ph-file-text', color: '#16a34a' };
  if (n.match(/\.pptx?$/)) return { icon: 'ph-fill ph-presentation', color: '#dc2626' };
  if (n.match(/\.(jpg|jpeg|png|gif|webp|svg)$/)) return { icon: 'ph-fill ph-image', color: '#7c3aed' };
  if (n.match(/\.(mp4|mov|avi|mkv|webm)$/)) return { icon: 'ph-fill ph-video', color: '#fc8181' };
  if (n.match(/\.(mp3|wav|aac|flac|ogg)$/)) return { icon: 'ph-fill ph-music-notes', color: '#68d391' };
  if (n.match(/\.(zip|rar|7z|tar|gz)$/)) return { icon: 'ph-fill ph-file-archive', color: '#7c2d12' };
  if (n.match(/\.(js|py|ts|html|css|json|xml|sh|java|cpp|c)$/)) return { icon: 'ph-fill ph-file-code', color: '#ca8a04' };
  if (n.match(/\.(txt|md|csv|log)$/)) return { icon: 'ph-fill ph-file-text', color: '#64748b' };
  return { icon: 'ph-fill ph-file', color: '#79c0ff' };
}

export function getFileEmoji(ext) {
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

export function isImage(name) { return /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(name); }
export function isPDF(name) { return /\.pdf$/i.test(name); }
export function isText(name) { return /\.(txt|md|csv|log|json|xml|html|css|js|ts|py|sh|java|yaml|yml)$/i.test(name); }

export function formatDate(timestamp) {
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

export function getFileUrl(apiBase, filePath) {
  const encoded = filePath.split('/').map(encodeURIComponent).join('/');
  return `${apiBase}/download/${encoded}`;
}
