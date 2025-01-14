import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    
    # 记住密码相关配置
    REMEMBER_COOKIE_NAME = 'remember_token'  # Cookie名称
    REMEMBER_COOKIE_DURATION = timedelta(days=30)  # Cookie保存30天
    REMEMBER_COOKIE_SECURE = False  # 是否只在HTTPS下发送Cookie
    REMEMBER_COOKIE_HTTPONLY = True  # 防止Cookie被JavaScript访问
    REMEMBER_COOKIE_REFRESH_EACH_REQUEST = True  # 每次请求都刷新Cookie时间
    REMEMBER_COOKIE_PATH = '/'  # Cookie路径