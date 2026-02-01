import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Loader2 } from 'lucide-react';
import { useWorkflowStore } from '../store/workflowStore';
import Step1TextSplit from '../components/steps/Step1TextSplit';
import Step2SegmentProcess from '../components/steps/Step2SegmentProcess';
import Step5VideoMerge from '../components/steps/Step5VideoMerge';

export default function WorkflowPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { currentWorkflow, loadingWorkflow, loadWorkflow, clearCurrentWorkflow } = useWorkflowStore();

  useEffect(() => {
    if (id) {
      loadWorkflow(id);
    }
    return () => {
      clearCurrentWorkflow();
    };
  }, [id, loadWorkflow, clearCurrentWorkflow]);

  if (loadingWorkflow) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!currentWorkflow) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <p className="text-gray-500 mb-4">工作流不存在</p>
        <button
          onClick={() => navigate('/')}
          className="text-blue-600 hover:underline"
        >
          返回首页
        </button>
      </div>
    );
  }

  const steps = [
    { title: '文案拆分', component: Step1TextSplit },
    { title: '片段处理', component: Step2SegmentProcess },
    { title: '视频合成', component: Step5VideoMerge },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => navigate('/')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{currentWorkflow.name}</h1>
          <p className="text-sm text-gray-500">
            创建于 {new Date(currentWorkflow.created_at).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-6">
        {steps.map((step, index) => {
          const StepComponent = step.component;
          return (
            <div key={index} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <h2 className="font-medium text-gray-900">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-600 text-white text-sm mr-2">
                    {index + 1}
                  </span>
                  {step.title}
                </h2>
              </div>
              <div className="p-4">
                <StepComponent />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
