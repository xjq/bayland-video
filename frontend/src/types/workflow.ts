export interface Segment {
  index: number;
  original: string;
  prompt: string | null;
  image_url: string | null;
  video_url: string | null;
  video_status: 'pending' | 'generating' | 'completed' | 'failed';
  video_task_id: string | null;
}

export interface Workflow {
  id: string;
  name: string;
  created_at: string;
  updated_at?: string;
  original_text: string;
  segments: Segment[];
  final_video_url: string | null;
  status: 'draft' | 'processing' | 'completed' | 'failed';
}

export interface WorkflowSummary {
  id: string;
  name: string;
  created_at: string;
  status: string;
  segment_count: number;
}
