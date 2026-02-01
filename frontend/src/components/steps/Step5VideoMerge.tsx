import { Combine, Loader2, AlertCircle, Download, Video } from 'lucide-react';
import { useWorkflowStore } from '../../store/workflowStore';
import { workflowService } from '../../services/workflowService';

export default function Step5VideoMerge() {
  const { currentWorkflow, processing, errors, mergeVideos } = useWorkflowStore();

  if (!currentWorkflow?.segments || currentWorkflow.segments.length === 0) {
    return (
      <p className="text-gray-500 text-center py-4">
        请先完成前面的步骤
      </p>
    );
  }

  const allVideosCompleted = currentWorkflow.segments.every(s => s.video_status === 'completed' && s.video_url);
  const isMerging = processing['merge'];
  const error = errors['merge'];

  const handleMerge = async () => {
    try {
      await mergeVideos();
    } catch {
      // 错误已在store中处理
    }
  };

  const handleDownload = () => {
    if (currentWorkflow.final_video_url) {
      // 如果是完整URL，直接打开
      if (currentWorkflow.final_video_url.startsWith('http')) {
        window.open(currentWorkflow.final_video_url, '_blank');
      } else {
        // 否则使用API下载
        window.location.href = workflowService.getDownloadUrl(currentWorkflow.id);
      }
    }
  };

  return (
    <div className="space-y-4">
      {!allVideosCompleted ? (
        <div className="text-center py-8">
          <Video className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">
            请先完成第四步：生成所有视频片段
          </p>
          <p className="text-sm text-gray-400 mt-2">
            已完成 {currentWorkflow.segments.filter(s => s.video_status === 'completed').length} / {currentWorkflow.segments.length} 个片段
          </p>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              所有视频片段已生成完成，点击按钮合成完整视频
            </p>
            {!currentWorkflow.final_video_url && (
              <button
                onClick={handleMerge}
                disabled={isMerging}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {isMerging ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    合成中...
                  </>
                ) : (
                  <>
                    <Combine className="w-4 h-4" />
                    合成完整视频
                  </>
                )}
              </button>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}

          {isMerging && (
            <div className="flex flex-col items-center justify-center py-12 bg-gray-50 rounded-lg">
              <Loader2 className="w-12 h-12 text-green-500 animate-spin mb-4" />
              <p className="text-gray-600">正在合成视频，请稍候...</p>
              <p className="text-sm text-gray-400 mt-1">这可能需要几分钟时间</p>
            </div>
          )}

          {currentWorkflow.final_video_url && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-700 font-medium">视频合成完成！</p>
              </div>

              <video
                src={currentWorkflow.final_video_url}
                controls
                className="w-full rounded-lg shadow-lg"
              />

              <div className="flex gap-3">
                <button
                  onClick={handleDownload}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Download className="w-5 h-5" />
                  下载视频
                </button>
                <button
                  onClick={handleMerge}
                  disabled={isMerging}
                  className="flex items-center gap-2 px-4 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  <Combine className="w-5 h-5" />
                  重新合成
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
