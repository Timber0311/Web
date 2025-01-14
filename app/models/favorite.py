from app import db
from app.models.base import TimestampMixin

class Favorite(db.Model, TimestampMixin):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    resource = db.relationship('Resource', backref=db.backref('favorites', lazy=True)) 