from datetime import datetime, date, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models.favorite import Favorite
from app.models.point_record import PointRecord
from app.models.checkin import Checkin
from app.models.base import TimestampMixin
from app.utils.time_utils import get_current_time

class User(UserMixin, db.Model, TimestampMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_reviewer = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password) 
    
    def has_favorited(self, resource):
        """检查用户是否收藏了指定资源"""
        return Favorite.query.filter_by(
            user_id=self.id,
            resource_id=resource.id
        ).first() is not None 
    
    def unread_notifications_count(self):
        from app.models.notification import Notification
        return Notification.query.filter_by(user_id=self.id, is_read=False).count() 
    
    def is_administrator(self):
        return self.is_admin 
    
    def add_points(self, amount, reason, resource=None):
        """
        添加积分并记录
        """
        self.points += amount
        record = PointRecord(
            user_id=self.id,
            amount=amount,
            reason=reason,
            related_resource_id=resource.id if resource else None
        )
        db.session.add(record)
        db.session.commit()
    
    def deduct_points(self, amount, reason, resource=None):
        """
        扣除积分并记录
        """
        if self.points >= amount:
            self.points -= amount
            record = PointRecord(
                user_id=self.id,
                amount=-amount,
                reason=reason,
                related_resource_id=resource.id if resource else None
            )
            db.session.add(record)
            db.session.commit()
            return True
        return False 
    
    def can_checkin(self):
        """检查今天是否可以签到"""
        today = get_current_time().date()
        return not Checkin.query.filter_by(
            user_id=self.id,
            checkin_date=today
        ).first()
    
    def get_consecutive_checkin_days(self):
        """获取连续签到天数"""
        today = get_current_time().date()
        consecutive_days = 0
        current_date = today - timedelta(days=1)  # 从昨天开始查
        
        while True:
            checkin = Checkin.query.filter_by(
                user_id=self.id,
                checkin_date=current_date
            ).first()
            
            if not checkin:
                break
            
            consecutive_days += 1
            current_date -= timedelta(days=1)
        
        return consecutive_days
    
    def do_checkin(self):
        """执行签到"""
        if not self.can_checkin():
            return False
        
        consecutive_days = self.get_consecutive_checkin_days()
        points = Checkin.get_points(consecutive_days)
        
        checkin = Checkin(
            user_id=self.id,
            checkin_date=get_current_time().date(),
            points=points
        )
        
        db.session.add(checkin)
        self.add_points(points, f'第{consecutive_days + 1}天连续签到奖励')
        return True 
    
    def get_id(self):
        return str(self.id)
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False 
    
    def has_downloaded(self, resource):
        """检查用户是否下载过指定资源"""
        return self.downloads.filter_by(resource_id=resource.id).first() is not None
    
    def is_super_admin(self):
        """判断是否为超级管理员（admin）"""
        return self.username == 'admin'