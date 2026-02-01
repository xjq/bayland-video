import { create } from 'zustand';
import type { Workflow, WorkflowSummary, Segment } from '../types';
import { workflowService } from '../services/workflowService';

interface WorkflowState {
  // 工作流列表
  workflows: WorkflowSummary[];
  loadingList: boolean;

  // 当前工作流
  currentWorkflow: Workflow | null;
  loadingWorkflow: boolean;

  // 操作状态
  processing: Record<string, boolean>;
  errors: Record<string, string>;

  // 工作流列表操作
  fetchWorkflows: () => Promise<void>;
  createWorkflow: (name?: string) => Promise<Workflow>;
  deleteWorkflow: (id: string) => Promise<void>;

  // 当前工作流操作
  loadWorkflow: (id: string) => Promise<void>;
  clearCurrentWorkflow: () => void;
  updateSegment: (idx: number, updates: Partial<Segment>) => void;

  // 视频生成流程
  splitText: (text: string) => Promise<void>;
  optimizePrompt: (idx: number, text?: string) => Promise<void>;
  uploadImage: (idx: number, file: File) => Promise<void>;
  generateVideo: (idx: number) => Promise<void>;
  generateAllVideos: () => Promise<void>;
  checkVideoStatus: (idx: number) => Promise<void>;
  mergeVideos: () => Promise<void>;

  // 工具方法
  setProcessing: (key: string, value: boolean) => void;
  setError: (key: string, error: string | null) => void;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  workflows: [],
  loadingList: false,
  currentWorkflow: null,
  loadingWorkflow: false,
  processing: {},
  errors: {},

  fetchWorkflows: async () => {
    set({ loadingList: true });
    try {
      const workflows = await workflowService.getWorkflows();
      set({ workflows });
    } catch (error) {
      console.error('获取工作流列表失败:', error);
    } finally {
      set({ loadingList: false });
    }
  },

  createWorkflow: async (name?: string) => {
    const workflow = await workflowService.createWorkflow(name);
    await get().fetchWorkflows();
    return workflow;
  },

  deleteWorkflow: async (id: string) => {
    await workflowService.deleteWorkflow(id);
    await get().fetchWorkflows();
  },

  loadWorkflow: async (id: string) => {
    set({ loadingWorkflow: true, currentWorkflow: null });
    try {
      const workflow = await workflowService.getWorkflow(id);
      set({ currentWorkflow: workflow });
    } catch (error) {
      console.error('加载工作流失败:', error);
      throw error;
    } finally {
      set({ loadingWorkflow: false });
    }
  },

  clearCurrentWorkflow: () => {
    set({ currentWorkflow: null, errors: {}, processing: {} });
  },

  updateSegment: (idx: number, updates: Partial<Segment>) => {
    const { currentWorkflow } = get();
    if (!currentWorkflow) return;

    const newSegments = [...currentWorkflow.segments];
    newSegments[idx] = { ...newSegments[idx], ...updates };
    set({
      currentWorkflow: { ...currentWorkflow, segments: newSegments }
    });
  },

  splitText: async (text: string) => {
    const { currentWorkflow, setProcessing, setError } = get();
    if (!currentWorkflow) return;

    setProcessing('split', true);
    setError('split', null);

    try {
      const result = await workflowService.splitText(currentWorkflow.id, text);
      set({
        currentWorkflow: {
          ...currentWorkflow,
          original_text: text,
          segments: result.segments
        }
      });
    } catch (error) {
      setError('split', (error as Error).message);
      throw error;
    } finally {
      setProcessing('split', false);
    }
  },

  optimizePrompt: async (idx: number, text?: string) => {
    const { currentWorkflow, setProcessing, setError, updateSegment } = get();
    if (!currentWorkflow) return;

    const key = `optimize-${idx}`;
    setProcessing(key, true);
    setError(key, null);

    try {
      const result = await workflowService.optimizePrompt(currentWorkflow.id, idx, text);
      updateSegment(idx, { prompt: result.prompt });
    } catch (error) {
      setError(key, (error as Error).message);
      throw error;
    } finally {
      setProcessing(key, false);
    }
  },

  uploadImage: async (idx: number, file: File) => {
    const { currentWorkflow, setProcessing, setError, updateSegment } = get();
    if (!currentWorkflow) return;

    const key = `upload-${idx}`;
    setProcessing(key, true);
    setError(key, null);

    try {
      const result = await workflowService.uploadImage(currentWorkflow.id, idx, file);
      updateSegment(idx, { image_url: result.image_url });
    } catch (error) {
      setError(key, (error as Error).message);
      throw error;
    } finally {
      setProcessing(key, false);
    }
  },

  generateVideo: async (idx: number) => {
    const { currentWorkflow, setProcessing, setError, updateSegment } = get();
    if (!currentWorkflow) return;

    const key = `generate-${idx}`;
    setProcessing(key, true);
    setError(key, null);

    try {
      const result = await workflowService.generateVideo(currentWorkflow.id, idx);
      updateSegment(idx, {
        video_task_id: result.task_id,
        video_status: 'generating'
      });
    } catch (error) {
      setError(key, (error as Error).message);
      throw error;
    } finally {
      setProcessing(key, false);
    }
  },

  generateAllVideos: async () => {
    const { currentWorkflow, generateVideo } = get();
    if (!currentWorkflow) return;

    for (let i = 0; i < currentWorkflow.segments.length; i++) {
      const segment = currentWorkflow.segments[i];
      if (segment.prompt && segment.video_status !== 'completed') {
        await generateVideo(i);
      }
    }
  },

  checkVideoStatus: async (idx: number) => {
    const { currentWorkflow, updateSegment } = get();
    if (!currentWorkflow) return;

    try {
      const result = await workflowService.getVideoStatus(currentWorkflow.id, idx);
      updateSegment(idx, {
        video_status: result.status,
        video_url: result.video_url || currentWorkflow.segments[idx].video_url
      });
    } catch (error) {
      console.error(`检查视频状态失败 (片段 ${idx}):`, error);
    }
  },

  mergeVideos: async () => {
    const { currentWorkflow, setProcessing, setError } = get();
    if (!currentWorkflow) return;

    setProcessing('merge', true);
    setError('merge', null);

    try {
      const result = await workflowService.mergeVideos(currentWorkflow.id);
      set({
        currentWorkflow: {
          ...currentWorkflow,
          final_video_url: result.final_video_url,
          status: 'completed'
        }
      });
    } catch (error) {
      setError('merge', (error as Error).message);
      throw error;
    } finally {
      setProcessing('merge', false);
    }
  },

  setProcessing: (key: string, value: boolean) => {
    set((state) => ({
      processing: { ...state.processing, [key]: value }
    }));
  },

  setError: (key: string, error: string | null) => {
    set((state) => ({
      errors: error
        ? { ...state.errors, [key]: error }
        : Object.fromEntries(Object.entries(state.errors).filter(([k]) => k !== key))
    }));
  }
}));
