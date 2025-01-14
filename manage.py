from flask.cli import FlaskGroup
from app import create_app, db
from app.init_db import init_db

cli = FlaskGroup(create_app=create_app)

@cli.command('init-db')
def init_db_command():
    """初始化数据库"""
    init_db()
    print('数据库初始化完成')

@cli.command('create-admin')
def create_admin():
    """创建管理员账户"""
    from app.models.user import User
    
    email = input('请输入管理员邮箱: ')
    username = input('请输入管理员用户名: ')
    password = input('请输入管理员密码: ')
    
    user = User(email=email, username=username, points=1000)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    print('管理员账户创建成功')

@cli.command('clear-users')
def clear_users():
    """清空用户数据"""
    if input('此操作将删除所有用户数据(管理员除外)，是否继续? (y/n): ').lower() != 'y':
        print('操作已取消')
        return
        
    try:
        from app.models.user import User
        from app.models.resource import Resource
        from app.models.comment import Comment
        from app.models.favorite import Favorite
        from app.models.point_record import PointRecord
        from app.models.notification import Notification
        from app.models.checkin import Checkin
        
        # 删除非管理员用户相关的所有数据
        with create_app().app_context():
            # 获取非管理员用户的ID列表
            user_ids = [u.id for u in User.query.filter_by(is_admin=False).all()]
            
            if not user_ids:
                print('没有找到普通用户数据')
                return
                
            # 删除相关数据
            Notification.query.filter(Notification.user_id.in_(user_ids)).delete(synchronize_session=False)
            Comment.query.filter(Comment.user_id.in_(user_ids)).delete(synchronize_session=False)
            Favorite.query.filter(Favorite.user_id.in_(user_ids)).delete(synchronize_session=False)
            PointRecord.query.filter(PointRecord.user_id.in_(user_ids)).delete(synchronize_session=False)
            Checkin.query.filter(Checkin.user_id.in_(user_ids)).delete(synchronize_session=False)
            Resource.query.filter(Resource.user_id.in_(user_ids)).delete(synchronize_session=False)
            User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
            
            db.session.commit()
            print('用户数据清空成功')
            
    except Exception as e:
        print(f'清空数据失败: {str(e)}')
        db.session.rollback()

if __name__ == '__main__':
    cli() 