import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'

    # OSS配置
    OSS_ACCESS_KEY_ID = os.getenv('OSS_ACCESS_KEY_ID')
    OSS_ACCESS_KEY_SECRET = os.getenv('OSS_ACCESS_KEY_SECRET')
    OSS_ENDPOINT = os.getenv('OSS_ENDPOINT', 'oss-cn-hangzhou.aliyuncs.com')
    OSS_BUCKET_NAME = os.getenv('OSS_BUCKET_NAME')

    # OSS目录结构
    OSS_WORKFLOW_DIR = 'workflows/'
    OSS_IMAGE_DIR = 'images/'
    OSS_VIDEO_SEGMENT_DIR = 'segments/'
    OSS_VIDEO_FINAL_DIR = 'finals/'

    # 百炼API配置
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')

    # 模型配置
    TEXT_MODEL = os.getenv('TEXT_MODEL', 'qwen-max')  # 文本处理模型
    VIDEO_MODEL = os.getenv('VIDEO_MODEL', 'wanx2.1-i2v-turbo')  # 视频生成模型

    # 视频生成配置
    VIDEO_DURATION = int(os.getenv('VIDEO_DURATION', '5'))  # 视频时长（秒），支持1-5秒
    VIDEO_RESOLUTION = os.getenv('VIDEO_RESOLUTION', '1280*720')  # 分辨率
    VIDEO_PROMPT_EXTEND = os.getenv('VIDEO_PROMPT_EXTEND', 'true').lower() == 'true'  # 是否开启提示词优化

    # 本地存储配置（开发环境）
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOCAL_DATA_DIR = os.path.join(BASE_DIR, 'data')
    LOCAL_WORKFLOW_DIR = os.path.join(LOCAL_DATA_DIR, 'workflows')

    # 确保目录存在
    @staticmethod
    def init_app():
        os.makedirs(Config.LOCAL_WORKFLOW_DIR, exist_ok=True)
