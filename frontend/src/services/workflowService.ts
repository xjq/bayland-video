import api from './api';
import type { 
  Workflow, 
  WorkflowSummary, 
  SplitResponse, 
  OptimizeResponse,
  UploadImageResponse,
  GenerateVideoResponse,
  VideoStatusResponse,
  MergeResponse
} from '../types';

export const workflowService = {
  // 工作流管理
  async createWorkflow(name?: string): Promise<Workflow> {
    const { data } = await api.post('/workflow', { name });
    return data;
  },

  async getWorkflows(): Promise<WorkflowSummary[]> {
    const { data } = await api.get('/workflows');
    return data;
  },

  async getWorkflow(id: string): Promise<Workflow> {
    const { data } = await api.get(`/workflow/${id}`);
    return data;
  },

  async updateWorkflow(id: string, updates: Partial<Workflow>): Promise<Workflow> {
    const { data } = await api.put(`/workflow/${id}`, updates);
    return data;
  },

  async deleteWorkflow(id: string): Promise<void> {
    await api.delete(`/workflow/${id}`);
  },

  // 视频生成流程
  async splitText(workflowId: string, text: string): Promise<SplitResponse> {
    const { data } = await api.post(`/workflow/${workflowId}/split`, { text });
    return data;
  },

  async optimizePrompt(workflowId: string, segmentIdx: number, text?: string): Promise<OptimizeResponse> {
    const { data } = await api.post(`/workflow/${workflowId}/segment/${segmentIdx}/optimize`, { text });
    return data;
  },

  async uploadImage(workflowId: string, segmentIdx: number, file: File): Promise<UploadImageResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post(
      `/workflow/${workflowId}/segment/${segmentIdx}/upload-image`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  async generateVideo(workflowId: string, segmentIdx: number): Promise<GenerateVideoResponse> {
    const { data } = await api.post(`/workflow/${workflowId}/segment/${segmentIdx}/generate-video`);
    return data;
  },

  async getVideoStatus(workflowId: string, segmentIdx: number): Promise<VideoStatusResponse> {
    const { data } = await api.get(`/workflow/${workflowId}/segment/${segmentIdx}/video-status`);
    return data;
  },

  async mergeVideos(workflowId: string): Promise<MergeResponse> {
    const { data } = await api.post(`/workflow/${workflowId}/merge`);
    return data;
  },

  getDownloadUrl(workflowId: string): string {
    return `/api/workflow/${workflowId}/download`;
  }
};
