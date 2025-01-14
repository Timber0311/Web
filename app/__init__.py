from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import logging

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # 确保secret_key已设置
    if not app.secret_key:
        app.secret_key = Config.SECRET_KEY
    
    # 注册蓝图
    from app.routes import main, auth, user, resource, admin
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(resource.bp)
    app.register_blueprint(admin.bp)
    
    from app.commands import init_db_command
    app.cli.add_command(init_db_command)
    
    # 配置日志
    logging.basicConfig(level=logging.WARNING)  # 只显示警告及以上级别的日志
    
    # 关闭 Werkzeug 的请求日志
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)
    
    return app

from app.models.user import User

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 