from app import create_app, db
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == '__main__':
    try:
        # 确保上传文件夹存在
        import os
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # 创建数据库表
        with app.app_context():
            db.create_all()
        
        # 明确指定 host 和 port，并允许外部访问
        logger.info('Starting server on http://127.0.0.1:8080')
        app.run(
            host='0.0.0.0',  # 允许外部访问
            port=8080,
            debug=True
        )
    except Exception as e:
        logger.error(f'Failed to start server: {str(e)}') 