import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Video, Trash2, Clock, FileText } from 'lucide-react';
import { useWorkflowStore } from '../store/workflowStore';

export default function HomePage() {
  const navigate = useNavigate();
  const { workflows, loadingList, fetchWorkflows, createWorkflow, deleteWorkflow } = useWorkflowStore();
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const workflow = await createWorkflow();
      navigate(`/workflow/${workflow.id}`);
    } catch (error) {
      console.error('创建工作流失败:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('确定要删除这个工作流吗？')) {
      await deleteWorkflow(id);
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, { text: string; color: string }> = {
      draft: { text: '草稿', color: 'bg-gray-100 text-gray-600' },
      processing: { text: '处理中', color: 'bg-blue-100 text-blue-600' },
      completed: { text: '已完成', color: 'bg-green-100 text-green-600' },
      failed: { text: '失败', color: 'bg-red-100 text-red-600' }
    };
    return labels[status] || labels.draft;
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">口播视频生成器</h1>
          <p className="text-gray-500 mt-1">将文案转换为专业口播视频</p>
        </div>
        <button
          onClick={handleCreate}
          disabled={creating}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          <Plus className="w-5 h-5" />
          {creating ? '创建中...' : '新建工作流'}
        </button>
      </div>

      {/* Workflow List */}
      {loadingList ? (
        <div className="text-center py-12 text-gray-500">加载中...</div>
      ) : workflows.length === 0 ? (
        <div className="text-center py-12">
          <Video className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">还没有工作流，点击上方按钮创建一个</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workflows.map((workflow) => {
            const status = getStatusLabel(workflow.status);
            return (
              <div
                key={workflow.id}
                onClick={() => navigate(`/workflow/${workflow.id}`)}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 truncate">
                      {workflow.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-2 text-sm text-gray-500">
                      <Clock className="w-4 h-4" />
                      <span>{new Date(workflow.created_at).toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-sm text-gray-500">
                      <FileText className="w-4 h-4" />
                      <span>{workflow.segment_count} 个片段</span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDelete(e, workflow.id)}
                    className="p-2 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                    title="删除"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
                <div className="mt-3">
                  <span className={`inline-block px-2 py-1 text-xs rounded-full ${status.color}`}>
                    {status.text}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
