export type MediaType = "video" | "audio" | "image" | "playlist" | "gallery";

export type JobStatus =
  | "QUEUED"
  | "ANALYZING"
  | "DOWNLOADING"
  | "PROCESSING"
  | "PACKAGING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "EXPIRED";

export interface MediaFormatOption {
  format_id: string;
  label: string; // e.g. "1080p Full HD" or "320 kbps (High Quality)"
  extension: string; // "mp4", "mp3", "webm", etc.
  quality?: string; // "1080p", "720p", "320k"
  resolution?: string; // "1920x1080"
  filesize_approx?: number; // bytes
  has_video: boolean;
  has_audio: boolean;
  is_best?: boolean;
  vcodec?: string;
  acodec?: string;
  fps?: number;
}

export interface MediaImageItem {
  id: string;
  url: string;
  preview_url: string;
  title?: string;
  width?: number;
  height?: number;
  format?: string;
  filesize?: number;
  index: number;
}

export interface PlaylistItem {
  id: string;
  url: string;
  title: string;
  thumbnail?: string;
  duration?: number;
  uploader?: string;
  index: number;
}

export interface ExtractionResult {
  success: boolean;
  url: string;
  type: MediaType;
  title: string;
  thumbnail: string;
  duration?: number;
  uploader?: string;
  platform?: string;
  description?: string;
  video_formats: MediaFormatOption[];
  audio_formats: MediaFormatOption[];
  images: MediaImageItem[];
  playlist_items: PlaylistItem[];
  total_items?: number;
  created_at: string;
}

export interface JobProgressEvent {
  job_id: string;
  status: JobStatus;
  progress: number; // 0 - 100
  downloaded_bytes: number;
  total_bytes: number;
  speed: number; // bytes / sec
  eta: number; // seconds
  stage_message: string;
  filename?: string;
  mime_type?: string;
  download_url?: string;
  error_code?: string;
  error_message?: string;
}

export interface CreateJobRequest {
  url: string;
  media_type: MediaType;
  format_id?: string;
  audio_bitrate?: string;
  selected_image_indices?: number[];
  selected_playlist_indices?: number[];
  target_extension?: string;
}
