import os
import subprocess
import tempfile
import requests
from typing import List


class VideoService:
    """视频处理服务"""

    def download_video(self, url: str, save_path: str) -> bool:
        """从URL下载视频"""
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"下载视频失败: {e}")
            return False

    def merge_videos(self, video_files: List[str], output_path: str) -> bool:
        """使用ffmpeg合成多个视频片段"""
        if not video_files:
            return False

        # 创建临时concat文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            concat_file = f.name
            for video_file in video_files:
                # 使用正斜杠并转义路径
                safe_path = video_file.replace('\\', '/')
                f.write(f"file '{safe_path}'\n")

        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 执行ffmpeg命令
            cmd = [
                'C:\\ffmpeg-8.0.1-essentials_build\\bin\\ffmpeg',
                '-y',  # 覆盖输出文件
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',  # 直接复制流，不重新编码
                output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                print(f"ffmpeg错误: {result.stderr}")
                return False

            return os.path.exists(output_path)

        except subprocess.TimeoutExpired:
            print("视频合成超时")
            return False
        except Exception as e:
            print(f"视频合成失败: {e}")
            return False
        finally:
            # 清理临时文件
            if os.path.exists(concat_file):
                os.remove(concat_file)

    def cleanup_temp_files(self, file_paths: List[str]):
        """清理临时文件"""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"清理文件失败 {path}: {e}")
