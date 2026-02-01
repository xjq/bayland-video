import os
import tempfile
import requests
from flask import Blueprint, request, jsonify, send_file
from ..services.workflow_service import WorkflowService
from ..services.bailian_service import BailianService
from ..services.oss_service import get_oss_service
from ..services.video_service import VideoService
from ..config import Config

video_bp = Blueprint('video', __name__)
workflow_service = WorkflowService()
bailian_service = BailianService()
video_service = VideoService()


@video_bp.route('/api/workflow/<workflow_id>/split', methods=['POST'])
def split_text(workflow_id):
    """拆分原始文案"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404

    data = request.get_json()
    original_text = data.get('text', '')
    
    if not original_text:
        return jsonify({"error": "文案内容不能为空"}), 400

    try:
        segments = bailian_service.split_text(original_text)
        
        # 更新工作流
        segment_list = []
        for idx, text in enumerate(segments):
            segment_list.append({
                "index": idx,
                "original": text,
                "prompt": None,
                "image_url": None,
                "video_url": None,
                "video_status": "pending",
                "video_task_id": None
            })

        workflow_service.update_workflow(workflow_id, {
            "original_text": original_text,
            "segments": segment_list,
            "status": "draft"
        })

        return jsonify({
            "segments": segment_list
        })

    except Exception as e:
        return jsonify({"error": f"文案拆分失败: {str(e)}"}), 500


@video_bp.route('/api/workflow/<workflow_id>/segment/<int:idx>/optimize', methods=['POST'])
def optimize_prompt(workflow_id, idx):
    """优化片段提示词"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404

    if idx >= len(workflow.get('segments', [])):
        return jsonify({"error": "片段索引无效"}), 400

    data = request.get_json()
    segment_text = data.get('text', workflow['segments'][idx]['original'])

    try:
        prompt = bailian_service.optimize_to_prompt2(segment_text)

        # 更新片段
        workflow['segments'][idx]['original'] = segment_text
        workflow['segments'][idx]['prompt'] = prompt
        workflow_service.update_workflow(workflow_id, {
            "segments": workflow['segments']
        })

        return jsonify({
            "prompt": prompt
        })

    except Exception as e:
        return jsonify({"error": f"提示词优化失败: {str(e)}"}), 500


@video_bp.route('/api/workflow/<workflow_id>/segment/<int:idx>/upload-image', methods=['POST'])
def upload_image(workflow_id, idx):
    """上传首帧图片"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404

    if idx >= len(workflow.get('segments', [])):
        return jsonify({"error": "片段索引无效"}), 400

    if 'file' not in request.files:
        return jsonify({"error": "未找到上传文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    try:
        image_data = file.read()
        
        oss = get_oss_service()
        if oss:
            # 上传到OSS，保存OSS路径用于视频生成API
            oss_path = oss.get_image_path(workflow_id, idx)
            oss.upload_file(oss_path, image_data, 'image/jpeg')
            # 存储OSS路径（内部使用）
            oss_url = oss.get_public_url(oss_path)
        else:
            # 本地存储
            local_dir = os.path.join(Config.LOCAL_DATA_DIR, 'images', workflow_id)
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, f'segment_{idx}.jpg')
            with open(local_path, 'wb') as f:
                f.write(image_data)
            oss_url = None

        # 前端显示用代理URL
        display_url = f"/api/image/{workflow_id}/{idx}"

        # 更新工作流：存储OSS URL用于视频生成，前端用代理URL
        workflow['segments'][idx]['image_url'] = display_url
        workflow['segments'][idx]['image_oss_url'] = oss_url  # 视频生成API用
        workflow_service.update_workflow(workflow_id, {
            "segments": workflow['segments']
        })

        return jsonify({
            "image_url": display_url
        })

    except Exception as e:
        return jsonify({"error": f"图片上传失败: {str(e)}"}), 500


@video_bp.route('/api/workflow/<workflow_id>/segment/<int:idx>/generate-video', methods=['POST'])
def generate_video(workflow_id, idx):
    """提交视频生成任务（i2v图生视频模式）"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404

    if idx >= len(workflow.get('segments', [])):
        return jsonify({"error": "片段索引无效"}), 400

    segment = workflow['segments'][idx]
    prompt = segment.get('prompt')
    
    if not prompt:
        return jsonify({"error": "请先生成提示词"}), 400

    if not segment.get('image_url'):
        return jsonify({"error": "i2v模式需要先上传首帧图片"}), 400

    # 生成OSS签名URL供百炼API访问（有效期5分钟）
    oss = get_oss_service()
    if oss:
        oss_path = oss.get_image_path(workflow_id, idx)
        image_url = oss.get_signed_url(oss_path, expires=300)
        print(f"[DEBUG] 视频生成使用的图片URL: {image_url}")  # 调试日志
    else:
        return jsonify({"error": "本地模式不支持视频生成，请配置OSS"}), 400

    try:
        result = bailian_service.submit_video_task(prompt, image_url)

        if not result['success']:
            return jsonify({"error": result['error']}), 500

        # 更新片段状态
        workflow['segments'][idx]['video_task_id'] = result['task_id']
        workflow['segments'][idx]['video_status'] = 'generating'
        workflow_service.update_workflow(workflow_id, {
            "segments": workflow['segments'],
            "status": "processing"
        })

        return jsonify({
            "task_id": result['task_id'],
            "status": "generating"
        })

    except Exception as e:
        return jsonify({"error": f"提交视频生成任务失败: {str(e)}"}), 500


@video_bp.route('/api/workflow/<workflow_id>/segment/<int:idx>/video-status', methods=['GET'])
def get_video_status(workflow_id, idx):
    """查询视频生成状态"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404

    if idx >= len(workflow.get('segments', [])):
        return jsonify({"error": "片段索引无效"}), 400

    segment = workflow['segments'][idx]
    task_id = segment.get('video_task_id')

    if not task_id:
        return jsonify({
            "status": segment.get('video_status', 'pending'),
            "video_url": segment.get('video_url')
        })

    try:
        result = bailian_service.query_video_task(task_id)
        
        # 更新状态
        workflow['segments'][idx]['video_status'] = result['status']
        
        if result['status'] == 'completed' and result.get('video_url'):
            video_url = result['video_url']
            
            # 将视频转存到OSS
            oss = get_oss_service()
            if oss:
                try:
                    # 下载视频
                    response = requests.get(video_url, timeout=300)
                    if response.status_code == 200:
                        # 上传到OSS
                        oss_path = oss.get_video_segment_path(workflow_id, idx)
                        oss.upload_file(oss_path, response.content, 'video/mp4')
                        workflow['segments'][idx]['video_url'] = f"/api/video/{workflow_id}/{idx}"
                        workflow['segments'][idx]['video_oss_path'] = oss_path
                        print(f"视频转存OSS成功: {oss_path}")
                    else:
                        # 下载失败
                        workflow['segments'][idx]['video_status'] = 'failed'
                        print(f"视频下载失败: HTTP {response.status_code}")
                except Exception as e:
                    # 转存失败
                    workflow['segments'][idx]['video_status'] = 'failed'
                    print(f"视频转存OSS失败: {e}")
            else:
                # 没有OSS配置
                workflow['segments'][idx]['video_status'] = 'failed'
                print("视频转存失败: OSS未配置")

        workflow_service.update_workflow(workflow_id, {
            "segments": workflow['segments']
        })

        return jsonify({
            "status": result['status'],
            "video_url": workflow['segments'][idx].get('video_url'),
            "error": result.get('error')
        })

    except Exception as e:
        return jsonify({"error": f"查询状态失败: {str(e)}"}), 500


@video_bp.route('/api/workflow/<workflow_id>/merge', methods=['POST'])
def merge_videos(workflow_id):
    """合成完整视频"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404

    segments = workflow.get('segments', [])
    if not segments:
        return jsonify({"error": "没有视频片段"}), 400

    # 检查所有片段是否都有视频
    for seg in segments:
        if not seg.get('video_url'):
            return jsonify({"error": f"片段 {seg['index']} 尚未生成视频"}), 400

    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        video_files = []
        oss = get_oss_service()

        # 下载所有视频片段
        for i, seg in enumerate(segments):
            local_path = os.path.join(temp_dir, f'segment_{i}.mp4')
            video_url = seg.get('video_url', '')
            
            # 检查是否是内部代理路径
            if video_url.startswith('/api/video/'):
                # 从 OSS 获取
                if oss:
                    # 优先使用存储的 oss_path，否则根据规则生成
                    oss_path = seg.get('video_oss_path') or oss.get_video_segment_path(workflow_id, i)
                    try:
                        video_data = oss.download_file(oss_path)
                        with open(local_path, 'wb') as f:
                            f.write(video_data)
                        video_files.append(local_path)
                        continue
                    except Exception as e:
                        print(f"从OSS下载视频失败: {e}")
                
                # 尝试从本地获取
                local_video_path = os.path.join(
                    Config.LOCAL_DATA_DIR, 'videos', 
                    f'{workflow_id}_segment_{i}.mp4'
                )
                if os.path.exists(local_video_path):
                    import shutil
                    shutil.copy(local_video_path, local_path)
                    video_files.append(local_path)
                    continue
                
                return jsonify({"error": f"无法获取片段 {i} 的视频文件"}), 500
            else:
                # 外部URL，使用requests下载
                if video_service.download_video(video_url, local_path):
                    video_files.append(local_path)
                else:
                    return jsonify({"error": f"下载片段 {i} 失败"}), 500

        # 合成视频
        output_path = os.path.join(temp_dir, 'final.mp4')
        success = video_service.merge_videos(video_files, output_path)

        if not success:
            return jsonify({"error": "视频合成失败"}), 500

        # 上传到OSS或保存到本地
        oss = get_oss_service()
        if oss:
            with open(output_path, 'rb') as f:
                oss.upload_final_video(workflow_id, f.read())
            # 使用代理URL而不是OSS直链
            final_url = f"/api/final-video/{workflow_id}"
        else:
            # 本地存储
            final_dir = os.path.join(Config.LOCAL_DATA_DIR, 'finals')
            os.makedirs(final_dir, exist_ok=True)
            final_local = os.path.join(final_dir, f'{workflow_id}.mp4')
            
            import shutil
            shutil.copy(output_path, final_local)
            final_url = f"/api/final-video/{workflow_id}"

        # 更新工作流
        workflow_service.update_workflow(workflow_id, {
            "final_video_url": final_url,
            "status": "completed"
        })

        # 清理临时文件
        video_service.cleanup_temp_files(video_files + [output_path])
        os.rmdir(temp_dir)

        return jsonify({
            "final_video_url": final_url
        })

    except Exception as e:
        return jsonify({"error": f"视频合成失败: {str(e)}"}), 500


@video_bp.route('/api/workflow/<workflow_id>/download', methods=['GET'])
def download_video(workflow_id):
    """下载完整视频"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        return jsonify({"error": "工作流不存在"}), 404

    final_url = workflow.get('final_video_url')
    if not final_url:
        return jsonify({"error": "视频尚未合成"}), 400

    download_name = f'{workflow.get("name", workflow_id)}.mp4'
    
    # 代理路径，从本地或OSS获取
    if final_url.startswith('/api/'):
        # 先检查本地
        local_path = os.path.join(Config.LOCAL_DATA_DIR, 'finals', f'{workflow_id}.mp4')
        if os.path.exists(local_path):
            return send_file(
                local_path,
                mimetype='video/mp4',
                as_attachment=True,
                download_name=download_name
            )
        
        # 从OSS获取
        oss = get_oss_service()
        if oss:
            try:
                from io import BytesIO
                oss_path = oss.get_final_video_path(workflow_id)
                video_data = oss.download_file(oss_path)
                return send_file(
                    BytesIO(video_data),
                    mimetype='video/mp4',
                    as_attachment=True,
                    download_name=download_name
                )
            except Exception as e:
                print(f"下载视频失败: {e}")
        
        return jsonify({"error": "视频文件不存在"}), 404

    # 外部URL (不应该出现这种情况)
    return jsonify({"error": "无效的视频URL"}), 400


# 本地文件访问接口（开发环境用）
@video_bp.route('/api/local/image/<workflow_id>/<int:idx>', methods=['GET'])
def get_local_image(workflow_id, idx):
    """获取本地存储的图片"""
    local_path = os.path.join(Config.LOCAL_DATA_DIR, 'images', workflow_id, f'segment_{idx}.jpg')
    if os.path.exists(local_path):
        return send_file(local_path, mimetype='image/jpeg')
    return jsonify({"error": "图片不存在"}), 404


@video_bp.route('/api/local/video/<workflow_id>', methods=['GET'])
def get_local_video(workflow_id):
    """获取本地存储的完整视频"""
    local_path = os.path.join(Config.LOCAL_DATA_DIR, 'finals', f'{workflow_id}.mp4')
    if os.path.exists(local_path):
        return send_file(local_path, mimetype='video/mp4')
    return jsonify({"error": "视频不存在"}), 404


@video_bp.route('/api/image/<workflow_id>/<int:idx>', methods=['GET'])
def get_image(workflow_id, idx):
    """获取图片（代理接口，支持本地和OSS）"""
    # 先检查本地
    local_path = os.path.join(Config.LOCAL_DATA_DIR, 'images', workflow_id, f'segment_{idx}.jpg')
    if os.path.exists(local_path):
        return send_file(local_path, mimetype='image/jpeg')
    
    # 从OSS获取
    oss = get_oss_service()
    if oss:
        try:
            oss_path = oss.get_image_path(workflow_id, idx)
            image_data = oss.download_file(oss_path)
            from io import BytesIO
            return send_file(BytesIO(image_data), mimetype='image/jpeg')
        except Exception:
            pass
    
    return jsonify({"error": "图片不存在"}), 404


@video_bp.route('/api/video/<workflow_id>/<int:idx>', methods=['GET'])
def get_video(workflow_id, idx):
    """获取视频片段（代理接口，支持本地和OSS）"""
    from io import BytesIO
    
    # 先检查本地
    local_path = os.path.join(Config.LOCAL_DATA_DIR, 'segments', workflow_id, f'segment_{idx}.mp4')
    if os.path.exists(local_path):
        return send_file(local_path, mimetype='video/mp4')
    
    # 从OSS获取
    oss = get_oss_service()
    if oss:
        try:
            oss_path = oss.get_video_segment_path(workflow_id, idx)
            video_data = oss.download_file(oss_path)
            return send_file(BytesIO(video_data), mimetype='video/mp4')
        except Exception as e:
            print(f"获取视频失败: {e}")
    
    return jsonify({"error": "视频不存在"}), 404


@video_bp.route('/api/final-video/<workflow_id>', methods=['GET'])
def get_final_video(workflow_id):
    """获取合成后的完整视频（代理接口，支持本地和OSS）"""
    from io import BytesIO
    
    # 先检查本地
    local_path = os.path.join(Config.LOCAL_DATA_DIR, 'finals', f'{workflow_id}.mp4')
    if os.path.exists(local_path):
        return send_file(local_path, mimetype='video/mp4')
    
    # 从OSS获取
    oss = get_oss_service()
    if oss:
        try:
            oss_path = oss.get_final_video_path(workflow_id)
            video_data = oss.download_file(oss_path)
            return send_file(BytesIO(video_data), mimetype='video/mp4')
        except Exception as e:
            print(f"获取完整视频失败: {e}")
    
    return jsonify({"error": "视频不存在"}), 404
