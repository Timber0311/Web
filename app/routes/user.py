from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from app.models.resource import Resource
from app.models.point_record import PointRecord
from app.models.checkin import Checkin
from app.models.favorite import Favorite
from app.models.download import Download
from app.models.notification import Notification
from datetime import date
from sqlalchemy.sql import func
from app import db
from app.utils.time import get_network_time
import logging

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/profile')
@login_required
def profile():
    # 获取分页参数
    uploads_page = request.args.get('uploads_page', 1, type=int)
    favorites_page = request.args.get('favorites_page', 1, type=int)
    downloads_page = request.args.get('downloads_page', 1, type=int)
    points_page = request.args.get('points_page', 1, type=int)
    
    # 查询用户上传的资源
    uploads = Resource.query.filter_by(user_id=current_user.id)\
        .order_by(Resource.created_at.desc())\
        .paginate(page=uploads_page, per_page=10)
    
    # 查询用户收藏的资源
    favorites = Favorite.query.filter_by(user_id=current_user.id)\
        .order_by(Favorite.created_at.desc())\
        .paginate(page=favorites_page, per_page=10)
        
    # 查询用户下载记录
    downloads = Download.query.filter_by(user_id=current_user.id)\
        .order_by(Download.created_at.desc())\
        .paginate(page=downloads_page, per_page=10)
        
    # 查询积分记录
    point_records = PointRecord.query.filter_by(user_id=current_user.id)\
        .order_by(PointRecord.created_at.desc())\
        .paginate(page=points_page, per_page=10)
    
    return render_template('user/profile.html',
                         uploads=uploads,
                         favorites=favorites,
                         downloads=downloads,
                         point_records=point_records)

@bp.route('/points')
@login_required
def points():
    page = request.args.get('page', 1, type=int)
    records = PointRecord.query.filter_by(user_id=current_user.id)\
        .order_by(PointRecord.created_at.desc())\
        .paginate(page=page, per_page=20)
    return render_template('user/points.html', records=records)

@bp.route('/checkin', methods=['POST'])
@login_required
def checkin():
    if current_user.do_checkin():
        flash('签到成功')
    else:
        flash('今天已经签到过了')
    return redirect(url_for('user.profile'))

@bp.route('/checkin-status')
@login_required
def checkin_status():
    try:
        today = date.today()
        checkin = Checkin.query.filter_by(
            user_id=current_user.id,
            checkin_date=today
        ).first()
        
        # 使用本地时间作为备选
        current_time = get_network_time()
        
        data = {
            'can_checkin': not bool(checkin),
            'consecutive_days': current_user.get_consecutive_checkin_days(),
            'today_checked': bool(checkin)
        }
        return jsonify(data)
    except Exception as e:
        logging.warning(f"签到状态检查失败: {str(e)}")
        return jsonify({'can_checkin': False, 'error': '系统繁忙'})

@bp.route('/checkin-history')
@login_required
def checkin_history():
    page = request.args.get('page', 1, type=int)
    checkins = Checkin.query.filter_by(user_id=current_user.id)\
        .order_by(Checkin.checkin_date.desc())\
        .paginate(page=page, per_page=20)
    
    # 获取本月签到天数
    current_month = date.today().replace(day=1)
    monthly_checkins = Checkin.query.filter(
        Checkin.user_id == current_user.id,
        Checkin.checkin_date >= current_month
    ).count()
    
    # 获取累计获得的签到积分
    total_points = db.session.query(func.sum(Checkin.points))\
        .filter_by(user_id=current_user.id)\
        .scalar() or 0
    
    return render_template('user/checkin_history.html',
                         checkins=checkins,
                         consecutive_days=current_user.get_consecutive_checkin_days(),
                         monthly_checkins=monthly_checkins,
                         total_points=total_points)

@bp.route('/checkin-calendar')
@login_required
def checkin_calendar():
    # 获取年月参数，默认为当前月
    today = date.today()
    year = request.args.get('year', today.year, type=int)
    month = request.args.get('month', today.month, type=int)
    
    # 获取用户当月的签到记录
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    
    checkins = Checkin.query.filter(
        Checkin.user_id == current_user.id,
        Checkin.checkin_date >= start_date,
        Checkin.checkin_date < end_date
    ).all()
    
    # 转换为日期集合
    checkin_dates = {c.checkin_date for c in checkins}
    
    # 生成日历数据
    from app.utils.calendar import get_month_calendar
    calendar_data = get_month_calendar(year, month, checkin_dates)
    
    # 获取上个月和下个月的日期
    if month == 1:
        prev_year = year - 1
        prev_month = 12
    else:
        prev_year = year
        prev_month = month - 1
        
    if month == 12:
        next_year = year + 1
        next_month = 1
    else:
        next_year = year
        next_month = month + 1
    
    return render_template('user/checkin_calendar.html',
                         calendar_data=calendar_data,
                         year=year,
                         month=month,
                         prev_year=prev_year,
                         prev_month=prev_month,
                         next_year=next_year,
                         next_month=next_month) 

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # 表单验证
    if not all([current_password, new_password, confirm_password]):
        return jsonify({
            'success': False,
            'message': '请填写所有密码字段'
        })
    
    # 验证当前密码
    if not current_user.check_password(current_password):
        return jsonify({
            'success': False,
            'message': '当前密码错误'
        })
    
    # 验证新密码
    if len(new_password) < 8:
        return jsonify({
            'success': False,
            'message': '新密码长度不能少于8个字符'
        })
        
    if new_password != confirm_password:
        return jsonify({
            'success': False,
            'message': '两次输入的新密码不一致'
        })
        
    if current_password == new_password:
        return jsonify({
            'success': False,
            'message': '新密码不能与当前密码相同'
        })
    
    try:
        # 修改密码
        current_user.set_password(new_password)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '密码修改成功，请重新登录'
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'修改密码失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': '修改密码失败，请稍后重试'
        })

@bp.route('/notifications')
@login_required
def notifications():
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=10)
    
    # 标记所有未读通知为已读
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notification in unread:
        notification.is_read = True
    db.session.commit()
    
    return render_template('user/notifications.html', notifications=notifications)

@bp.route('/notification/<int:id>/delete', methods=['POST'])
@login_required
def delete_notification(id):
    notification = Notification.query.get_or_404(id)
    if notification.user_id != current_user.id:
        abort(403)
    
    db.session.delete(notification)
    db.session.commit()
    flash('通知已删除')
    return redirect(url_for('user.notifications')) 

@bp.route('/notifications/clear', methods=['POST'])
@login_required
def clear_all_notifications():
    try:
        Notification.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash('已清空所有通知')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'清空通知失败: {str(e)}')
        flash('清空通知失败，请稍后重试')
    
    return redirect(url_for('user.notifications')) 