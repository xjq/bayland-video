export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface SplitResponse {
  segments: import('./workflow').Segment[];
}

export interface OptimizeResponse {
  prompt: string;
}

export interface UploadImageResponse {
  image_url: string;
}

export interface GenerateVideoResponse {
  task_id: string;
  status: string;
}

export interface VideoStatusResponse {
  status: 'pending' | 'generating' | 'completed' | 'failed';
  video_url?: string;
  error?: string;
}

export interface MergeResponse {
  final_video_url: string;
}
