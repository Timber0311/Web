from app import db
from app.models.base import TimestampMixin

class Comment(db.Model, TimestampMixin):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id', ondelete='CASCADE'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('comments', lazy=True, cascade='all, delete-orphan'))
    resource = db.relationship('Resource', backref=db.backref('comments', lazy=True, cascade='all, delete-orphan')) 