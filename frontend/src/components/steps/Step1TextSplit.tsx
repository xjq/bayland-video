import { useState } from 'react';
import { Scissors, Loader2, AlertCircle } from 'lucide-react';
import { useWorkflowStore } from '../../store/workflowStore';

export default function Step1TextSplit() {
  const { currentWorkflow, processing, errors, splitText } = useWorkflowStore();
  const [text, setText] = useState(currentWorkflow?.original_text || '');

  const isProcessing = processing['split'];
  const error = errors['split'];

  const handleSplit = async () => {
    if (!text.trim()) return;
    try {
      await splitText(text);
    } catch {
      // 错误已在store中处理
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          输入完整口播文案
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="请输入您的口播文案，系统将自动将其拆分为适合15秒视频的片段..."
          className="w-full h-40 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          disabled={isProcessing}
        />
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-600 text-sm">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      <div className="flex items-center justify-between">
        <button
          onClick={handleSplit}
          disabled={!text.trim() || isProcessing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              拆分中...
            </>
          ) : (
            <>
              <Scissors className="w-4 h-4" />
              拆分文案
            </>
          )}
        </button>

        {currentWorkflow?.segments && currentWorkflow.segments.length > 0 && (
          <span className="text-sm text-gray-500">
            已拆分为 {currentWorkflow.segments.length} 个片段
          </span>
        )}
      </div>

      {/* 拆分结果预览 */}
      {currentWorkflow?.segments && currentWorkflow.segments.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium text-gray-700">拆分结果：</h4>
          {currentWorkflow.segments.map((segment, idx) => (
            <div
              key={idx}
              className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm"
            >
              <span className="text-gray-400 mr-2">#{idx + 1}</span>
              {segment.original}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
