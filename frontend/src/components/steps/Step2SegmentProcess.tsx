import { useEffect, useRef, useCallback } from 'react';
import { Wand2, Upload, Play, Loader2, AlertCircle, Check, Image, Video, RefreshCw, X } from 'lucide-react';
import { useWorkflowStore } from '../../store/workflowStore';

export default function Step2SegmentProcess() {
  const { 
    currentWorkflow, 
    processing, 
    errors, 
    optimizePrompt, 
    updateSegment,
    uploadImage,
    generateVideo,
    generateAllVideos,
    checkVideoStatus
  } = useWorkflowStore();
  
  const fileInputRefs = useRef<Record<number, HTMLInputElement | null>>({});
  const pollingRef = useRef<Record<number, NodeJS.Timeout>>({});

  // 轮询检查视频状态
  const startPolling = useCallback((idx: number) => {
    if (pollingRef.current[idx]) return;
    
    pollingRef.current[idx] = setInterval(async () => {
      await checkVideoStatus(idx);
      
      const segment = currentWorkflow?.segments[idx];
      if (segment?.video_status === 'completed' || segment?.video_status === 'failed') {
        clearInterval(pollingRef.current[idx]);
        delete pollingRef.current[idx];
      }
    }, 5000);
  }, [checkVideoStatus, currentWorkflow?.segments]);

  useEffect(() => {
    currentWorkflow?.segments.forEach((segment, idx) => {
      if (segment.video_status === 'generating' && !pollingRef.current[idx]) {
        startPolling(idx);
      }
    });

    return () => {
      Object.values(pollingRef.current).forEach(clearInterval);
      pollingRef.current = {};
    };
  }, [currentWorkflow?.segments, startPolling]);

  if (!currentWorkflow?.segments || currentWorkflow.segments.length === 0) {
    return (
      <p className="text-gray-500 text-center py-4">
        请先完成第一步：拆分文案
      </p>
    );
  }

  const handleOptimize = async (idx: number) => {
    try {
      await optimizePrompt(idx);
    } catch {
      // 错误已在store中处理
    }
  };

  const handleFileSelect = async (idx: number, file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件');
      return;
    }
    try {
      await uploadImage(idx, file);
    } catch {
      // 错误已在store中处理
    }
  };

  const handleRemoveImage = (idx: number) => {
    updateSegment(idx, { image_url: null });
  };

  const handleGenerate = async (idx: number) => {
    try {
      await generateVideo(idx);
      startPolling(idx);
    } catch {
      // 错误已在store中处理
    }
  };

  const handleGenerateAll = async () => {
    // 检查所有片段是否都有提示词和首帧图
    const canGenerate = currentWorkflow.segments.every(s => s.prompt && s.image_url);
    if (!canGenerate) {
      alert('请确保所有片段都已生成提示词并上传首帧图');
      return;
    }
    await generateAllVideos();
    currentWorkflow.segments.forEach((_, idx) => {
      if (currentWorkflow.segments[idx].video_status === 'generating') {
        startPolling(idx);
      }
    });
  };

  const allHavePrompts = currentWorkflow.segments.every(s => s.prompt);
  const allHaveImages = currentWorkflow.segments.every(s => s.image_url);
  const allCompleted = currentWorkflow.segments.every(s => s.video_status === 'completed');
  const anyGenerating = currentWorkflow.segments.some(s => s.video_status === 'generating');

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { text: string; className: string }> = {
      pending: { text: '待生成', className: 'bg-gray-100 text-gray-600' },
      generating: { text: '生成中', className: 'bg-blue-100 text-blue-600' },
      completed: { text: '已完成', className: 'bg-green-100 text-green-600' },
      failed: { text: '失败', className: 'bg-red-100 text-red-600' }
    };
    return badges[status] || badges.pending;
  };

  return (
    <div className="space-y-6">
      {/* 批量操作按钮 */}
      <div className="flex items-center justify-end gap-3">
        {allHavePrompts && allHaveImages && !allCompleted && (
          <button
            onClick={handleGenerateAll}
            disabled={anyGenerating}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Play className="w-4 h-4" />
            一键生成所有视频
          </button>
        )}
      </div>

      {/* 片段列表 */}
      {currentWorkflow.segments.map((segment, idx) => {
        const isOptimizing = processing[`optimize-${idx}`];
        const isUploading = processing[`upload-${idx}`];
        const isGenerating = processing[`generate-${idx}`] || segment.video_status === 'generating';
        const optimizeError = errors[`optimize-${idx}`];
        const uploadError = errors[`upload-${idx}`];
        const generateError = errors[`generate-${idx}`];
        const status = getStatusBadge(segment.video_status);

        return (
          <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden">
            {/* 片段头部 */}
            <div className="bg-blue-100 px-4 py-3 flex items-center justify-between border-b border-blue-300">
              <span className="font-medium text-gray-900">片段 #{idx + 1}</span>
              <span className={`px-2 py-1 text-xs rounded-full ${status.className}`}>
                {status.text}
              </span>
            </div>

            <div className="p-4 space-y-4">
              {/* 原始文案和视频提示词 - 水平排列 */}
              <div className="grid grid-cols-2 gap-4">
                {/* 原始文案 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">原始文案</label>
                  <textarea
                    value={segment.original}
                    onChange={(e) => updateSegment(idx, { original: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-y min-h-[120px]"
                    rows={6}
                  />
                </div>

                {/* 视频提示词 */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-sm font-medium text-gray-700">视频提示词</label>
                    <button
                      onClick={() => handleOptimize(idx)}
                      disabled={isOptimizing}
                      className="flex items-center gap-1 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50"
                    >
                      {isOptimizing ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Wand2 className="w-3 h-3" />
                      )}
                      {segment.prompt ? '重新生成' : '生成提示词'}
                    </button>
                  </div>
                  {segment.prompt ? (
                    <textarea
                      value={segment.prompt}
                      onChange={(e) => updateSegment(idx, { prompt: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-y min-h-[120px]"
                      rows={6}
                    />
                  ) : (
                    <div className="w-full px-3 py-10 border border-dashed border-gray-300 rounded-lg text-center text-sm text-gray-400 min-h-[120px] flex items-center justify-center">
                      点击上方按钮生成提示词
                    </div>
                  )}
                  {optimizeError && (
                    <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" /> {optimizeError}
                    </p>
                  )}
                </div>
              </div>

              {/* 首帧图片和视频预览 - 并排显示 */}
              <div className="grid grid-cols-2 gap-4">
                {/* 首帧图片 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">首帧图片</label>
                  {segment.image_url ? (
                    <div className="relative group">
                      <div className="w-full h-48 bg-gray-100 rounded-lg border border-gray-200 flex items-center justify-center">
                        <img
                          src={segment.image_url}
                          alt={`片段 ${idx + 1} 首帧`}
                          className="max-w-full max-h-full object-contain"
                        />
                      </div>
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center gap-2">
                        <button
                          onClick={() => fileInputRefs.current[idx]?.click()}
                          className="p-2 bg-white rounded-full text-gray-700 hover:bg-gray-100"
                          title="更换图片"
                        >
                          <Upload className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleRemoveImage(idx)}
                          className="p-2 bg-white rounded-full text-red-500 hover:bg-gray-100"
                          title="删除图片"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div
                      onClick={() => fileInputRefs.current[idx]?.click()}
                      className="w-full h-48 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-colors"
                    >
                      {isUploading ? (
                        <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                      ) : (
                        <>
                          <Image className="w-6 h-6 text-gray-400 mb-1" />
                          <span className="text-xs text-gray-500">上传首帧图</span>
                        </>
                      )}
                    </div>
                  )}
                  <input
                    ref={(el) => (fileInputRefs.current[idx] = el)}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleFileSelect(idx, file);
                      e.target.value = '';
                    }}
                  />
                  {uploadError && (
                    <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" /> {uploadError}
                    </p>
                  )}
                </div>

                {/* 视频预览 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">生成视频</label>
                  {segment.video_url ? (
                    <div className="relative">
                      <div className="w-full h-48 bg-black rounded-lg border border-gray-200 flex items-center justify-center">
                        <video
                          src={segment.video_url}
                          controls
                          className="max-w-full max-h-full"
                        />
                      </div>
                      <button
                        onClick={() => handleGenerate(idx)}
                        disabled={isGenerating || !segment.prompt || !segment.image_url}
                        className="absolute bottom-2 right-2 p-1.5 bg-white/90 rounded-full text-gray-700 hover:bg-white disabled:opacity-50"
                        title="重新生成"
                      >
                        <RefreshCw className="w-3 h-3" />
                      </button>
                    </div>
                  ) : (
                    <div className="w-full h-48 border border-gray-200 rounded-lg flex flex-col items-center justify-center bg-gray-50">
                      {isGenerating ? (
                        <>
                          <Loader2 className="w-6 h-6 text-blue-500 animate-spin mb-1" />
                          <span className="text-xs text-gray-500">生成中...</span>
                        </>
                      ) : (
                        <>
                          <Video className="w-6 h-6 text-gray-300 mb-1" />
                          <button
                            onClick={() => handleGenerate(idx)}
                            disabled={!segment.prompt || !segment.image_url}
                            className="mt-1 px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            生成视频
                          </button>
                          {(!segment.prompt || !segment.image_url) && (
                            <span className="text-xs text-gray-400 mt-1">
                              需要提示词和首帧图
                            </span>
                          )}
                        </>
                      )}
                    </div>
                  )}
                  {generateError && (
                    <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" /> {generateError}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
