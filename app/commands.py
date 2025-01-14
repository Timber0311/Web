import click
from flask.cli import with_appcontext
from app import db
from app.models.user import User
from app.models.category import Category

@click.command('init-db')
@with_appcontext
def init_db_command():
    """初始化数据库"""
    # 删除所有表
    db.drop_all()
    # 创建所有表
    db.create_all()
    
    # 创建管理员账号
    admin = User(
        username='admin',
        email='admin@example.com',
        is_admin=True,
        is_reviewer=True
    )
    admin.set_password('admin')
    db.session.add(admin)
    
    # 创建基础分类
    categories = [
        Category(name='课程资料'),
        Category(name='考试资料'),
        Category(name='编程代码'),
        Category(name='学习笔记')
    ]
    for category in categories:
        db.session.add(category)
        
    db.session.commit()
    click.echo('数据库初始化完成!') 