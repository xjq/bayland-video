from flask import Blueprint, request, jsonify
from ..services.workflow_service import WorkflowService

workflow_bp = Blueprint('workflow', __name__)
workflow_service = WorkflowService()


@workflow_bp.route('/api/workflow', methods=['POST'])
def create_workflow():
    """创建新工作流"""
    data = request.get_json() or {}
    name = data.get('name')
    
    workflow = workflow_service.create_workflow(name)
    return jsonify(workflow), 201


@workflow_bp.route('/api/workflows', methods=['GET'])
def get_workflows():
    """获取全部工作流列表"""
    workflows = workflow_service.list_workflows()
    return jsonify(workflows)


@workflow_bp.route('/api/workflow/<workflow_id>', methods=['GET'])
def get_workflow(workflow_id):
    """获取单个工作流详情"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404
    return jsonify(workflow)


@workflow_bp.route('/api/workflow/<workflow_id>', methods=['PUT'])
def update_workflow(workflow_id):
    """更新工作流"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "请求体不能为空"}), 400
    
    workflow = workflow_service.update_workflow(workflow_id, data)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404
    return jsonify(workflow)


@workflow_bp.route('/api/workflow/<workflow_id>', methods=['DELETE'])
def delete_workflow(workflow_id):
    """删除工作流"""
    success = workflow_service.delete_workflow(workflow_id)
    if not success:
        return jsonify({"error": "工作流不存在"}), 404
    return jsonify({"message": "删除成功"})
