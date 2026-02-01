import uuid
import json
import os
from datetime import datetime
from typing import List, Optional
from ..config import Config
from .oss_service import get_oss_service


class WorkflowService:
    """工作流管理服务"""

    def __init__(self):
        self.workflow_dir = Config.LOCAL_WORKFLOW_DIR

    def _get_workflow_path(self, workflow_id: str) -> str:
        return os.path.join(self.workflow_dir, f"{workflow_id}.json")

    def _get_oss_workflow_path(self, workflow_id: str) -> str:
        return f"{Config.OSS_WORKFLOW_DIR}{workflow_id}.json"

    def create_workflow(self, name: Optional[str] = None) -> dict:
        """创建新工作流"""
        workflow_id = str(uuid.uuid4())
        if not name:
            name = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        workflow = {
            "id": workflow_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "original_text": "",
            "segments": [],
            "final_video_url": None,
            "status": "draft"
        }

        self._save_workflow(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[dict]:
        """获取工作流详情（优先从本地获取，本地没有再从OSS获取）"""
        # 先从本地获取
        path = self._get_workflow_path(workflow_id)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 本地没有，尝试从OSS获取
        oss = get_oss_service()
        if oss:
            try:
                oss_path = self._get_oss_workflow_path(workflow_id)
                data = oss.download_file(oss_path)
                workflow = json.loads(data.decode('utf-8'))
                # 同步到本地缓存
                self._save_local(workflow)
                return workflow
            except Exception as e:
                print(f"从OSS获取工作流失败: {e}")
        
        return None

    def update_workflow(self, workflow_id: str, data: dict) -> Optional[dict]:
        """更新工作流"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None

        # 更新允许的字段
        allowed_fields = ['name', 'original_text', 'segments', 'final_video_url', 'status']
        for field in allowed_fields:
            if field in data:
                workflow[field] = data[field]

        workflow['updated_at'] = datetime.now().isoformat()
        self._save_workflow(workflow)
        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        deleted = False
        
        # 删除本地文件
        path = self._get_workflow_path(workflow_id)
        if os.path.exists(path):
            os.remove(path)
            deleted = True
        
        # 删除OSS文件
        oss = get_oss_service()
        if oss:
            try:
                oss_path = self._get_oss_workflow_path(workflow_id)
                oss.delete_file(oss_path)
                deleted = True
            except Exception:
                pass
        
        return deleted

    def list_workflows(self) -> List[dict]:
        """列出所有工作流（从OSS获取）"""
        workflows = []
        
        oss = get_oss_service()
        if oss:
            try:
                import oss2
                # 遍历OSS中的工作流文件
                prefix = Config.OSS_WORKFLOW_DIR
                for obj in oss2.ObjectIterator(oss.bucket, prefix=prefix):
                    if obj.key.endswith('.json'):
                        try:
                            data = oss.download_file(obj.key)
                            workflow = json.loads(data.decode('utf-8'))
                            workflows.append({
                                "id": workflow["id"],
                                "name": workflow["name"],
                                "created_at": workflow["created_at"],
                                "status": workflow.get("status", "draft"),
                                "segment_count": len(workflow.get("segments", []))
                            })
                        except Exception as e:
                            print(f"读取工作流失败 {obj.key}: {e}")
            except Exception as e:
                print(f"从OSS获取工作流列表失败: {e}")

        # 按创建时间降序排序
        workflows.sort(key=lambda x: x["created_at"], reverse=True)
        return workflows

    def _save_workflow(self, workflow: dict):
        """保存工作流到本地和OSS"""
        # 保存到本地
        self._save_local(workflow)
        
        # 上传到OSS
        oss = get_oss_service()
        if oss:
            try:
                oss_path = self._get_oss_workflow_path(workflow["id"])
                data = json.dumps(workflow, ensure_ascii=False, indent=2).encode('utf-8')
                oss.upload_file(oss_path, data, 'application/json')
            except Exception as e:
                print(f"上传工作流到OSS失败: {e}")

    def _save_local(self, workflow: dict):
        """保存工作流到本地"""
        path = self._get_workflow_path(workflow["id"])
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
