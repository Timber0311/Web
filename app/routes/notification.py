from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models.notification import Notification
from app import db

bp = Blueprint('notification', __name__, url_prefix='/notifications')

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=20)
    
    # 标记所有未读通知为已读
    unread = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in unread:
        notification.is_read = True
    
    db.session.commit()
    
    return render_template('notification/index.html', notifications=notifications)

@bp.route('/<int:id>/read')
@login_required
def mark_as_read(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(url_for('notification.index'))

@bp.route('/read-all')
@login_required
def mark_all_as_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({Notification.is_read: True})
    db.session.commit()
    return redirect(url_for('notification.index')) 