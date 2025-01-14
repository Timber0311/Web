from app import db
from app.utils.time_utils import get_current_time
from app.models.base import TimestampMixin

class Download(db.Model, TimestampMixin):
    __tablename__ = 'downloads'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('downloads', lazy='dynamic'))
    resource = db.relationship('Resource', backref=db.backref('downloads', lazy='dynamic')) 