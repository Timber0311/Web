from app import db
from app.models.base import TimestampMixin

class PointRecord(db.Model, TimestampMixin):
    __tablename__ = 'point_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # 正数表示获得，负数表示消耗
    reason = db.Column(db.String(100), nullable=False)  # 积分变动原因
    related_resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'))  # 相关资源ID
    
    user = db.relationship('User', backref=db.backref('point_records', lazy=True))
    related_resource = db.relationship('Resource', backref=db.backref('point_records', lazy=True)) 