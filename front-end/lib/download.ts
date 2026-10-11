/**
 * Client-Side YouTube Download Utility
 * 
 * Handles direct browser downloads from YouTube's streaming servers.
 * Uses the user's IP and cookies, bypassing server-side bot verification.
 * 
 * Supports:
 * - Progressive formats (single URL with video+audio) - direct download
 * - Adaptive formats (separate video/audio URLs) - opens in new tab for browser download
 * - HLS/DASH manifests - attempts to play in browser for "Save As"
 */

export type DownloadMethod = 'direct' | 'adaptive' | 'manifest' | 'fallback';

export interface DownloadOptions {
  format: {
    format_id: string;
    label: string;
    extension: string;
    url?: string;
    video_url?: string;
    audio_url?: string;
    manifest_url?: string;
    protocol?: string;
    has_video: boolean;
    has_audio: boolean;
  };
  title: string;
  onProgress?: (progress: number) => void;
  onError?: (error: string) => void;
  onComplete?: () => void;
}

export interface DownloadResult {
  method: DownloadMethod;
  success: boolean;
  message: string;
}

/**
 * Sanitize filename for download
 */
function sanitizeFilename(name: string, extension: string): string {
  return name
    .replace(/[<>:"/\\|?*\x00-\x1F]/g, '_')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 200) + `.${extension}`;
}

/**
 * Trigger browser download via anchor element
 */
function triggerDownload(url: string, filename: string): Promise<boolean> {
  return new Promise((resolve) => {
    try {
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.rel = 'noopener noreferrer';
      a.target = '_blank';
      
      // For same-origin, use click. For cross-origin, need to open in new tab
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      // Give browser time to start download
      setTimeout(() => resolve(true), 100);
    } catch {
      resolve(false);
    }
  });
}

/**
 * Open URL in new tab for browser to handle download
 */
function openInNewTab(url: string, filename: string): void {
  const newTab = window.open(url, '_blank', 'noopener,noreferrer');
  if (!newTab) {
    // Popup blocked - fallback to anchor
    triggerDownload(url, filename);
  }
}

/**
 * Check if URL is likely to support CORS/download
 */
function canDirectDownload(url: string): boolean {
  try {
    const u = new URL(url);
    // googlevideo.com often blocks CORS, but browser "Save As" works
    // Direct anchor download works for same-origin or when server allows
    return true; // Let browser try
  } catch {
    return false;
  }
}

/**
 * Main download function - tries multiple methods
 */
export async function downloadDirect(options: DownloadOptions): Promise<DownloadResult> {
  const { format, title, onProgress, onError, onComplete } = options;
  const filename = sanitizeFilename(title, format.extension);

  // Method 1: Progressive format (single URL with video+audio)
  if (format.url && format.has_video && format.has_audio) {
    onProgress?.(10);
    const success = await triggerDownload(format.url, filename);
    if (success) {
      onComplete?.();
      return { method: 'direct', success: true, message: 'Download started' };
    }
  }

  // Method 2: Adaptive format - try video+audio merge via MediaRecorder (experimental)
  // For now, open both URLs in new tabs for user to download separately
  if (format.video_url && format.audio_url) {
    onProgress?.(10);
    const videoUrl = format.video_url;
    const audioUrl = format.audio_url;
    // Open video stream in new tab
    openInNewTab(videoUrl, `${filename.replace(`.${format.extension}`, '')}_video.${format.extension}`);
    // Open audio stream in new tab
    setTimeout(() => {
      openInNewTab(audioUrl, `${filename.replace(`.${format.extension}`, '')}_audio.${format.extension}`);
    }, 500);
    
    onComplete?.();
    return { 
      method: 'adaptive', 
      success: true, 
      message: 'Opened video and audio streams in new tabs. Use "Save As" on each, then merge with a video editor.' 
    };
  }

  // Method 3: HLS/DASH manifest - try to play in video element for "Save As"
  if (format.manifest_url) {
    onProgress?.(10);
    await playManifestForDownload(format.manifest_url, filename, format.extension);
    onComplete?.();
    return { 
      method: 'manifest', 
      success: true, 
      message: 'Opened stream in player. Right-click video → "Save video as..." to download.' 
    };
  }

  // Method 4: Fallback - open video page for browser extensions
  onError?.('Direct download not available for this format. Try a different quality or use a browser extension.');
  return { 
    method: 'fallback', 
    success: false, 
    message: 'Format not directly downloadable. Try "Best Quality" option or use browser extension.' 
  };
}

/**
 * Play HLS/DASH manifest in a video element for user to "Save As"
 */
async function playManifestForDownload(manifestUrl: string, filename: string, extension: string): Promise<void> {
  return new Promise((resolve) => {
    // Create a modal with video player
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed; top: 0; left: 0; width: 100%; height: 100%;
      background: rgba(0,0,0,0.9); z-index: 10000;
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      color: white; font-family: system-ui;
    `;
    
    const video = document.createElement('video');
    video.controls = true;
    video.style.maxWidth = '90vw';
    video.style.maxHeight = '70vh';
    video.crossOrigin = 'anonymous';
    
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.style.marginTop = '1rem';
    closeBtn.style.padding = '0.5rem 1rem';
    closeBtn.onclick = () => {
      document.body.removeChild(modal);
      resolve();
    };
    
    const instructions = document.createElement('p');
    instructions.textContent = 'Right-click the video and select "Save video as..." to download';
    instructions.style.marginBottom = '1rem';
    instructions.style.opacity = '0.8';
    
    modal.appendChild(instructions);
    modal.appendChild(video);
    modal.appendChild(closeBtn);
    document.body.appendChild(modal);
    
    // Try to load manifest
    if (manifestUrl.includes('.m3u8') || manifestUrl.includes('m3u8')) {
      // HLS - need hls.js
      if (typeof Hls !== 'undefined' && Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(manifestUrl);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        video.src = manifestUrl;
        video.play().catch(() => {});
      } else {
        instructions.textContent = 'HLS not supported in this browser. Open manifest URL directly: ' + manifestUrl;
        video.style.display = 'none';
      }
    } else if (manifestUrl.includes('.mpd') || manifestUrl.includes('dash')) {
      // DASH - need dash.js
      instructions.textContent = 'DASH manifest detected. Open in new tab: ' + manifestUrl;
      video.style.display = 'none';
    } else {
      // Try direct
      video.src = manifestUrl;
      video.play().catch(() => {});
    }
    
    // Close on escape
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        document.body.removeChild(modal);
        document.removeEventListener('keydown', handleEscape);
        resolve();
      }
    };
    document.addEventListener('keydown', handleEscape);
  });
}

declare const Hls: any;

/**
 * Get downloadable formats from extraction result
 */
export function getDownloadableFormats<T extends {
  url?: string;
  video_url?: string;
  audio_url?: string;
  manifest_url?: string;
  protocol?: string;
  has_video: boolean;
  has_audio: boolean;
}>(videoFormats: T[]) {
  return {
    // Progressive formats (ready for direct download)
    progressive: videoFormats.filter((f): f is T => Boolean(f.url && f.has_video && f.has_audio)),
    // Adaptive video-only (need separate audio)
    adaptiveVideo: videoFormats.filter((f): f is T => Boolean(f.video_url && f.has_video && !f.has_audio)),
    // Audio-only
    audio: videoFormats.filter((f): f is T => Boolean(f.url && !f.has_video && f.has_audio)),
    // Manifest-based
    manifest: videoFormats.filter((f): f is T => Boolean(f.manifest_url)),
  };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes?: number): string {
  if (!bytes) return 'Unknown size';
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}