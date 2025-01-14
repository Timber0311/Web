import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db, create_app
from app.models.user import User
from app.models.category import Category

def init_db():
    app = create_app()
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()
        
        # 创建管理员账号
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            is_reviewer=True  # 设置为复核员
        )
        admin.set_password('admin')
        db.session.add(admin)
        
        # 创建基础分类
        categories = [
                Category(name='课程资料'),
                Category(name='考试资料'),
                Category(name='实验报告'),
                Category(name='编程代码'),
                Category(name='电子书籍'),
                Category(name='学术论文'),
                Category(name='课程作业'),
                Category(name='其他资源')
        ]
        for category in categories:
            db.session.add(category)
            
        db.session.commit()
        print('数据库初始化完成!')

if __name__ == '__main__':
    init_db() 