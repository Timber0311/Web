from app import db
from app.utils.time_utils import get_current_time

class Checkin(db.Model):
    __tablename__ = 'checkins'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    checkin_date = db.Column(db.Date, default=lambda: get_current_time().date())
    points = db.Column(db.Integer, nullable=False)  # 获得的积分
    created_at = db.Column(db.DateTime, default=get_current_time)
    
    user = db.relationship('User', backref=db.backref('checkins', lazy=True))
    
    @staticmethod
    def get_points(consecutive_days):
        """根据连续签到天数计算积分"""
        if consecutive_days >= 7:
            return 10
        elif consecutive_days >= 3:
            return 5
        else:
            return 3 