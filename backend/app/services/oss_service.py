import os
import time
import oss2
from typing import Optional
from ..config import Config


# 全局单例
_oss_instance = None


def get_oss_service():
    """获取OSS服务单例"""
    global _oss_instance
    if _oss_instance is None:
        try:
            _oss_instance = OSSService()
        except ValueError:
            return None
    return _oss_instance


class OSSService:
    """阿里云OSS存储服务"""

    def __init__(self):
        if not Config.OSS_ACCESS_KEY_ID or not Config.OSS_ACCESS_KEY_SECRET:
            raise ValueError("OSS配置缺失，请检查环境变量")
        
        auth = oss2.Auth(Config.OSS_ACCESS_KEY_ID, Config.OSS_ACCESS_KEY_SECRET)
        endpoint = Config.OSS_ENDPOINT
        # 移除可能存在的协议前缀，使用标准格式
        if endpoint.startswith('http://'):
            endpoint = endpoint[7:]
        elif endpoint.startswith('https://'):
            endpoint = endpoint[8:]
        
        # 使用 HTTPS endpoint
        full_endpoint = f"https://{endpoint}"
        
        self._bucket = oss2.Bucket(
            auth, 
            full_endpoint, 
            Config.OSS_BUCKET_NAME,
            connect_timeout=30
        )
        self._endpoint = endpoint
        print(f"[OSS] 初始化成功: {full_endpoint}/{Config.OSS_BUCKET_NAME}")

    @property
    def bucket(self):
        return self._bucket

    def upload_file(self, oss_path: str, data: bytes, content_type: Optional[str] = None) -> str:
        """上传文件到OSS（带重试）"""
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type
        
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                self.bucket.put_object(oss_path, data, headers=headers)
                return self.get_public_url(oss_path)
            except oss2.exceptions.ServerError as e:
                last_error = e
                print(f"[OSS] 上传失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                last_error = e
                print(f"[OSS] 上传异常: {e}")
                break
        
        raise last_error if last_error else Exception("上传失败")

    def upload_local_file(self, oss_path: str, local_path: str) -> str:
        """上传本地文件到OSS"""
        self.bucket.put_object_from_file(oss_path, local_path)
        return self.get_public_url(oss_path)

    def download_file(self, oss_path: str) -> bytes:
        """从OSS下载文件"""
        result = self.bucket.get_object(oss_path)
        return result.read()

    def download_to_local(self, oss_path: str, local_path: str):
        """下载OSS文件到本地"""
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        self.bucket.get_object_to_file(oss_path, local_path)

    def delete_file(self, oss_path: str):
        """删除OSS文件"""
        self.bucket.delete_object(oss_path)

    def delete_folder(self, folder_path: str):
        """删除OSS文件夹下所有文件"""
        for obj in oss2.ObjectIterator(self.bucket, prefix=folder_path):
            self.bucket.delete_object(obj.key)

    def get_public_url(self, oss_path: str) -> str:
        """获取文件的公网访问URL"""
        return f"https://{Config.OSS_BUCKET_NAME}.{Config.OSS_ENDPOINT}/{oss_path}"

    def get_signed_url(self, oss_path: str, expires: int = 300) -> str:
        """获取签名URL（用于私有文件访问，百炼API需要）"""
        # 生成签名URL，确保使用HTTPS
        url = self.bucket.sign_url('GET', oss_path, expires, slash_safe=True)
        # 确保是HTTPS
        if url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        return url

    # 便捷方法
    def get_image_path(self, workflow_id: str, segment_idx: int) -> str:
        """生成图片存储路径"""
        return f"{Config.OSS_IMAGE_DIR}{workflow_id}/segment_{segment_idx}.jpg"

    def get_video_segment_path(self, workflow_id: str, segment_idx: int) -> str:
        """生成视频片段存储路径"""
        return f"{Config.OSS_VIDEO_SEGMENT_DIR}{workflow_id}/segment_{segment_idx}.mp4"

    def get_final_video_path(self, workflow_id: str) -> str:
        """生成完整视频存储路径"""
        return f"{Config.OSS_VIDEO_FINAL_DIR}{workflow_id}.mp4"

    def upload_image(self, workflow_id: str, segment_idx: int, image_data: bytes) -> str:
        """上传首帧图片"""
        oss_path = self.get_image_path(workflow_id, segment_idx)
        return self.upload_file(oss_path, image_data, 'image/jpeg')

    def upload_video_segment(self, workflow_id: str, segment_idx: int, video_data: bytes) -> str:
        """上传视频片段"""
        oss_path = self.get_video_segment_path(workflow_id, segment_idx)
        return self.upload_file(oss_path, video_data, 'video/mp4')

    def upload_final_video(self, workflow_id: str, video_data: bytes) -> str:
        """上传完整视频"""
        oss_path = self.get_final_video_path(workflow_id)
        return self.upload_file(oss_path, video_data, 'video/mp4')
