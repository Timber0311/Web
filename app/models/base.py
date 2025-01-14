from app import db
from app.utils.time_utils import get_current_time

class TimestampMixin:
    """时间戳Mixin，提供创建时间字段"""
    created_at = db.Column(db.DateTime, default=get_current_time) 