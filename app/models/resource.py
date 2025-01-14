from app import db
from datetime import datetime
from app.utils.time_utils import get_current_time
from app.models.base import TimestampMixin

class Resource(db.Model, TimestampMixin):
    __tablename__ = 'resources'
    
    # 状态常量
    STATUS_PENDING = 'pending'    # 待审核
    STATUS_APPROVED = 'approved'  # 已通过
    STATUS_REJECTED = 'rejected'  # 已拒绝
    STATUS_REVIEW = 'review'      # 待复核
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(20))
    points_required = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default=STATUS_PENDING)
    reject_reason = db.Column(db.Text)  # 拒绝原因
    review_time = db.Column(db.DateTime)  # 审核时间
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 审核人ID
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    
    user = db.relationship(
        'User', 
        backref=db.backref('uploaded_resources', lazy=True),
        foreign_keys=[user_id],
        primaryjoin="Resource.user_id == User.id"
    )
    category = db.relationship('Category', backref=db.backref('resources', lazy=True))
    reviewer = db.relationship(
        'User',
        backref=db.backref('reviewed_resources', lazy=True),
        foreign_keys=[reviewer_id],
        primaryjoin="Resource.reviewer_id == User.id"
    )
    
    def __repr__(self):
        return f'<Resource {self.title}>' 