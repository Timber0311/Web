from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.resource import Resource
from app.models.category import Category
from app.utils.decorators import admin_required, reviewer_required
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
import os
from app.models.comment import Comment
from app.models.favorite import Favorite
from app.models.point_record import PointRecord
from app.models.notification import Notification
from app.models.checkin import Checkin
from app.models.download import Download
from app.utils.notifications import (
    send_notification,
    notify_resource_approved,
    notify_resource_rejected,
    notify_resource_review_approved,
    notify_resource_review_rejected
)
from sqlalchemy import and_

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/')
@login_required
@admin_required
def index():
    # 获取统计数据
    stats = {
        'user_count': User.query.count(),
        'resource_count': Resource.query.count(),
        'today_upload': Resource.query.filter(
            Resource.created_at >= datetime.now().date()
        ).count(),
        'pending_count': Resource.query.filter_by(
            status=Resource.STATUS_PENDING
        ).count()
    }
    
    # 获取最新资源
    latest_resources = Resource.query.order_by(
        Resource.created_at.desc()
    ).limit(5).all()
    
    # 获取热门资源
    popular_resources = Resource.query.order_by(
        Resource.download_count.desc()
    ).limit(5).all()
    
    return render_template('admin/index.html',
                         stats=stats,
                         latest_resources=latest_resources,
                         popular_resources=popular_resources)

@bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)

@bp.route('/resources')
@login_required
@admin_required
def resources():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    category_id = request.args.get('category_id', type=int)
    
    query = Resource.query
    
    if status:
        query = query.filter_by(status=status)
    if category_id:
        query = query.filter_by(category_id=category_id)
        
    resources = query.order_by(Resource.created_at.desc()).paginate()
    
    stats = {
        'total': Resource.query.count(),
        'pending': Resource.query.filter_by(status='pending').count(),
        'review': Resource.query.filter_by(status='review').count(),
        'approved': Resource.query.filter_by(status='approved').count(),
        'rejected': Resource.query.filter_by(status='rejected').count()
    }
    
    return render_template('admin/resource.html',
                         resources=resources,
                         stats=stats,
                         status=status,
                         category_id=category_id)

@bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@bp.route('/category/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    name = request.form.get('name')
    parent_id = request.form.get('parent_id')
    
    if name:
        category = Category(name=name)
        if parent_id:
            category.parent_id = parent_id
        db.session.add(category)
        db.session.commit()
        flash('分类添加成功')
    return redirect(url_for('admin.categories'))

@bp.route('/resource/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_resource(id):
    resource = Resource.query.get_or_404(id)
    
    try:
        # 先删除与资源相关的所有记录
        Download.query.filter_by(resource_id=resource.id).delete()
        PointRecord.query.filter_by(related_resource_id=resource.id).delete()
        Comment.query.filter_by(resource_id=resource.id).delete()
        Favorite.query.filter_by(resource_id=resource.id).delete()
        
        # 删除资源文件
        if resource.file_path:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], resource.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # 最后删除资源记录
        db.session.delete(resource)
        db.session.commit()
        
        flash('资源删除成功')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除资源失败: {str(e)}')
        flash('删除资源失败，请稍后重试')
    
    return redirect(url_for('admin.resources'))

@bp.route('/user/<int:id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_admin(id):
    user = User.query.get_or_404(id)
    
    # 只有超级管理员可以修改管理员权限
    if not current_user.is_super_admin():
        flash('只有超级管理员可以修改管理员权限')
        return redirect(url_for('admin.users'))
    
    # 不能修改超级管理员
    if user.is_super_admin():
        flash('不能修改超级管理员的权限')
        return redirect(url_for('admin.users'))
    
    # 不能修改自己
    if user.id == current_user.id:
        flash('不能修改自己的管理员权限')
        return redirect(url_for('admin.users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    
    # 发送通知
    title = '管理员权限变更'
    content = f'您已被{"授予" if user.is_admin else "取消"}管理员权限'
    send_notification(user, title, content)
    
    flash(f'已{"授予" if user.is_admin else "取消"}管理员权限')
    return redirect(url_for('admin.users'))

@bp.route('/category/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_category(id):
    category = Category.query.get_or_404(id)
    name = request.form.get('name')
    parent_id = request.form.get('parent_id')
    
    try:
        if name:
            category.name = name
            if parent_id:
                # 检查是否形成循环依赖
                if int(parent_id) != category.id and not Category.would_create_cycle(category.id, int(parent_id)):
                    category.parent_id = int(parent_id)
                else:
                    flash('无法将分类设置为自身的子分类或形成循环依赖')
                    return redirect(url_for('admin.categories'))
            else:
                category.parent_id = None
                
            db.session.commit()
            flash('分类更新成功')
        else:
            flash('分类名称不能为空')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新分类失败: {str(e)}')
        flash('更新分类失败，请稍后重试')
        
    return redirect(url_for('admin.categories'))

@bp.route('/category/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    category = Category.query.get_or_404(id)
    if category.resources:
        flash('该分类下还有资源，无法删除')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('分类删除成功')
    return redirect(url_for('admin.categories'))

@bp.route('/resource/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_resource(id):
    resource = Resource.query.get_or_404(id)
    if resource.status != 'pending':
        flash('只能通过待审核的资源')
        return redirect(url_for('admin.resources'))
        
    resource.status = 'approved'
    resource.reviewer_id = current_user.id
    resource.review_time = datetime.now()
    db.session.commit()
    
    # 发送通知给资源上传者
    notify_resource_approved(resource)
    
    flash('资源已通过审核')
    return redirect(url_for('admin.resources'))

@bp.route('/resource/<int:id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_resource(id):
    resource = Resource.query.get_or_404(id)
    if resource.status != 'pending':
        flash('只能拒绝待审核的资源')
        return redirect(url_for('admin.resources'))
        
    reason = request.form.get('reason')
    if not reason:
        flash('请输入拒绝原因')
        return redirect(url_for('admin.resources'))
        
    resource.status = 'rejected'
    resource.reviewer_id = current_user.id
    resource.review_time = datetime.now()
    resource.reject_reason = reason
    db.session.commit()
    
    # 发送通知给资源上传者
    notify_resource_rejected(resource)
    
    flash('资源已拒绝')
    return redirect(url_for('admin.resources'))

# 添加资源统计路由
@bp.route('/stats')
@login_required
@admin_required
def stats():
    # 修改查询,使用正确的字段名 user_id
    active_users = db.session.query(
        User,
        func.count(Resource.id).label('upload_count'),
        func.sum(Resource.downloads).label('total_downloads')
    ).outerjoin(
        Resource, 
        and_(Resource.user_id == User.id)  # 使用 user_id 而不是 uploader_id
    ).group_by(
        User.id
    ).order_by(
        func.count(Resource.id).desc()
    ).limit(10).all()

    # 获取每日上传统计
    daily_uploads = db.session.query(
        func.date(Resource.created_at).label('date'),
        func.count(Resource.id).label('count')
    ).group_by(
        func.date(Resource.created_at)
    ).order_by(
        func.date(Resource.created_at).desc()
    ).limit(7).all()

    # 获取分类统计
    category_stats = db.session.query(
        Category.name,
        func.count(Resource.id).label('count')
    ).outerjoin(
        Resource,
        and_(Resource.category_id == Category.id)  # 明确指定连接条件
    ).group_by(
        Category.id
    ).order_by(
        func.count(Resource.id).desc()
    ).all()

    return render_template('admin/stats.html',
                         active_users=active_users,
                         daily_uploads=daily_uploads,
                         category_stats=category_stats)

@bp.route('/user/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # 不能删除自己（包括超级管理员）
    if user.id == current_user.id:
        flash('不能删除自己的账号')
        return redirect(url_for('admin.users'))
    
    # 普通管理员不能删除管理员
    if user.is_administrator() and not current_user.is_super_admin():
        flash('只有超级管理员可以删除管理员账号')
        return redirect(url_for('admin.users'))
    
    # 不能删除超级管理员（即使是超级管理员自己也不能删除超级管理员）
    if user.is_super_admin():
        flash('超级管理员账号不能被删除')
        return redirect(url_for('admin.users'))
    
    try:
        # 删除用户相关的所有数据
        Download.query.filter_by(user_id=user.id).delete()  # 先删除下载记录
        Notification.query.filter_by(user_id=user.id).delete()
        Comment.query.filter_by(user_id=user.id).delete()
        Favorite.query.filter_by(user_id=user.id).delete()
        PointRecord.query.filter_by(user_id=user.id).delete()
        Checkin.query.filter_by(user_id=user.id).delete()
        
        # 删除用户上传的资源文件
        for resource in Resource.query.filter_by(user_id=user.id).all():
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], resource.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        # 删除资源记录
        Resource.query.filter_by(user_id=user.id).delete()
        
        # 最后删除用户
        db.session.delete(user)
        db.session.commit()
        
        flash(f'用户 {user.username} 已被删除')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除用户失败: {str(e)}')
        flash('删除用户失败，请稍后重试')
    
    return redirect(url_for('admin.users'))

@bp.route('/user/<int:id>/points', methods=['POST'])
@login_required
@admin_required
def manage_points(id):
    user = User.query.get_or_404(id)
    
    # 只有超级管理员可以修改其他管理员的积分
    if user.is_administrator() and not current_user.is_super_admin():
        flash('只有超级管理员可以修改管理员的积分')
        return redirect(url_for('admin.users'))
    
    # 不能修改超级管理员的积分（除非是超级管理员自己）
    if user.is_super_admin() and not current_user.is_super_admin():
        flash('不能修改超级管理员的积分')
        return redirect(url_for('admin.users'))
        
    action = request.form.get('action')
    amount = request.form.get('amount', type=int)
    reason = request.form.get('reason')
    
    if not all([action, amount, reason]):
        flash('请填写完整的积分操作信息')
        return redirect(url_for('admin.users'))
        
    try:
        title = '积分变动通知'
        if action == 'add':
            user.add_points(amount, f'管理员操作：{reason}')
            content = f'管理员为您增加了 {amount} 积分，原因：{reason}'
            send_notification(user, title, content)
            flash(f'已为用户 {user.username} 增加 {amount} 积分')
            
        elif action == 'deduct':
            if user.points < amount:
                flash(f'用户积分不足，当前积分：{user.points}')
                return redirect(url_for('admin.users'))
            user.deduct_points(amount, f'管理员操作：{reason}')
            content = f'管理员扣除了您 {amount} 积分，原因：{reason}'
            send_notification(user, title, content)
            flash(f'已扣除用户 {user.username} {amount} 积分')
            
        elif action == 'clear':
            original_points = user.points
            user.points = 0
            db.session.add(PointRecord(
                user_id=user.id,
                amount=-original_points,
                reason=f'管理员操作：{reason}'
            ))
            content = f'管理员已清空您的积分，原因：{reason}'
            send_notification(user, title, content)
            flash(f'已清空用户 {user.username} 的积分')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'积分操作失败: {str(e)}')
        flash('积分操作失败，请稍后重试')
    
    return redirect(url_for('admin.users'))

@bp.route('/user/<int:id>/clear-point-records', methods=['POST'])
@login_required
@admin_required
def clear_point_records(id):
    user = User.query.get_or_404(id)
    
    # 只有超级管理员可以清空管理员的积分记录
    if user.is_administrator() and not current_user.is_super_admin():
        flash('只有超级管理员可以清空管理员的积分记录')
        return redirect(url_for('admin.users'))
    
    # 不能清空超级管理员的积分记录（除非是超级管理员自己）
    if user.is_super_admin() and not current_user.is_super_admin():
        flash('不能清空超级管理员的积分记录')
        return redirect(url_for('admin.users'))
    
    try:
        # 删除所有积分记录
        PointRecord.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        # 发送通知
        title = '积分记录清空通知'
        content = '管理员已清空您的所有积分记录'
        send_notification(user, title, content)
        
        flash(f'已清空用户 {user.username} 的积分记录')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'清空积分记录失败: {str(e)}')
        flash('清空积分记录失败，请稍后重试')
    
    return redirect(url_for('admin.users'))

@bp.route('/resource/<int:id>/review', methods=['POST'])
@login_required
@admin_required
def review_resource(id):
    resource = Resource.query.get_or_404(id)
    action = request.form.get('action')
    reason = request.form.get('reason', '')
    
    if action not in ['approve', 'reject']:
        flash('无效的操作')
        return redirect(url_for('admin.resources'))
    
    try:
        if action == 'approve':
            resource.status = Resource.STATUS_APPROVED
            resource.reject_reason = None
            notify_resource_approved(resource)
            flash('资源已通过审核')
        else:
            if not reason:
                flash('请填写拒绝原因')
                return redirect(url_for('admin.resources'))
            resource.status = Resource.STATUS_REJECTED
            resource.reject_reason = reason
            notify_resource_rejected(resource)
            flash('资源已被拒绝')
        
        resource.review_time = get_current_time()
        resource.reviewer_id = current_user.id
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'资源审核失败: {str(e)}')
        flash('操作失败，请稍后重试')
    
    return redirect(url_for('admin.resources'))

# 提交复核
@bp.route('/resource/<int:id>/submit-review', methods=['POST'])
@login_required
@admin_required
def submit_to_review(id):
    resource = Resource.query.get_or_404(id)
    # 只有已审核的资源（已通过或已拒绝）才能提交复核
    if resource.status not in ['approved', 'rejected']:
        return jsonify({'message': '只能对已审核的资源进行复核'}), 400
        
    resource.status = 'review'
    db.session.commit()
    
    # 可以添加通知等逻辑
    return jsonify({'message': '提交复核成功'})

# 通过复核
@bp.route('/resource/<int:id>/approve-review', methods=['POST'])
@login_required
@reviewer_required
def approve_review(id):
    resource = Resource.query.get_or_404(id)
    if resource.status != 'review':
        return jsonify({'message': '只能处理待复核的资源'}), 400
        
    resource.status = 'approved'
    resource.reviewer_id = current_user.id
    resource.review_time = datetime.now()
    db.session.commit()
    
    # 发送复核通过通知
    notify_resource_review_approved(resource)
    
    return redirect(url_for('admin.resources'))

# 拒绝复核
@bp.route('/resource/<int:id>/reject-review', methods=['POST'])
@login_required
@reviewer_required
def reject_review(id):
    resource = Resource.query.get_or_404(id)
    if resource.status != 'review':
        return jsonify({'message': '只能处理待复核的资源'}), 400
        
    reason = request.form.get('reason')
    if not reason:
        return jsonify({'message': '请输入拒绝原因'}), 400
        
    resource.status = 'rejected'
    resource.reviewer_id = current_user.id
    resource.review_time = datetime.now()
    resource.reject_reason = reason
    db.session.commit()
    
    # 发送复核拒绝通知
    notify_resource_review_rejected(resource)
    
    return redirect(url_for('admin.resources')) 