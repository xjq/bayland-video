from flask import Flask
from flask_cors import CORS
from .config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 初始化配置
    Config.init_app()
    
    # 注册蓝图
    from .routes.workflow_routes import workflow_bp
    from .routes.video_routes import video_bp
    
    app.register_blueprint(workflow_bp)
    app.register_blueprint(video_bp)
    
    return app
