from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.resource import Resource
from app.models.category import Category
from app import db
import os
from app.models.comment import Comment
from app.models.favorite import Favorite
from sqlalchemy import or_
from app.utils.notifications import notify_resource_comment, notify_resource_download
from app.models.download import Download
import time

bp = Blueprint('resource', __name__, url_prefix='/resource')

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {
    # 文档格式
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt',
    # 压缩包格式
    'zip', 'rar', '7z', 'tar', 'gz',
    # 图片格式
    'jpg', 'jpeg', 'png', 'gif',
    # 代码和数据格式
    'py', 'java', 'cpp', 'c', 'h', 'js', 'css', 'html', 'sql', 'json', 'xml',
    # 其他常用格式
    'csv', 'md', 'mp4', 'mp3'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # 检查是否有文件
        if 'file' not in request.files:
            flash('未选择文件')
            return redirect(request.url)
            
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            flash('未选择文件')
            return redirect(request.url)
            
        # 检查文件类型
        if not allowed_file(file.filename):
            flash(f'不支持的文件类型。支持的类型：{", ".join(ALLOWED_EXTENSIONS)}')
            return redirect(request.url)
            
        # 获取表单数据
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category')
        points = request.form.get('points', type=int, default=0)
        
        if not all([title, description, category_id]):
            flash('请填写所有必填字段')
            return redirect(request.url)
            
        try:
            # 安全处理文件名
            filename = secure_filename(file.filename)
            # 添加时间戳避免重名
            filename = f"{int(time.time())}_{filename}"
            
            # 确保上传目录存在
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
                
            # 保存文件
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # 创建资源记录
            resource = Resource(
                title=title,
                description=description,
                file_path=filename,
                file_type=filename.rsplit('.', 1)[1].lower(),
                points_required=points,
                user_id=current_user.id,
                category_id=category_id
            )
            
            db.session.add(resource)
            db.session.commit()
            
            flash('资源上传成功，等待管理员审核')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'资源上传失败: {str(e)}')
            flash('上传失败，请稍后重试')
            return redirect(request.url)
            
    # GET 请求显示上传表单
    categories = Category.query.all()
    return render_template('resource/upload.html', categories=categories)

@bp.route('/<int:id>')
def detail(id):
    resource = Resource.query.get_or_404(id)
    
    # 计算是否可以访问
    can_access = True
    if resource.status != 'approved':
        if not current_user.is_authenticated:
            can_access = False
        elif not (current_user.is_administrator() or current_user.id == resource.user_id):
            can_access = False
    
    # 计算是否可以下载
    can_download = True
    if not current_user.is_authenticated:
        can_download = False
    elif not current_user.is_administrator() and current_user.id != resource.user_id:
        if resource.points_required > current_user.points:
            can_download = False
    
    # 获取评论分页
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(resource_id=id)\
        .order_by(Comment.created_at.desc())\
        .paginate(page=page, per_page=10)
    
    return render_template('resource/detail.html',
                         resource=resource,
                         can_access=can_access,
                         can_download=can_download,
                         comments=comments)  # 添加评论数据

@bp.route('/download/<int:id>')
@login_required
def download(id):
    resource = Resource.query.get_or_404(id)
    
    # 检查资源状态
    if resource.status != 'approved':
        # 只有资源上传者和管理员可以下载未通过审核的资源
        if resource.user_id != current_user.id and not current_user.is_administrator():
            flash('该资源尚未通过审核，暂时无法下载')
            return redirect(url_for('resource.detail', id=id))
    
    # 检查是否已经下载过
    previous_download = Download.query.filter_by(
        user_id=current_user.id,
        resource_id=resource.id
    ).first()
    
    # 如果是资源上传者或已下载过，直接下载
    if current_user.id == resource.user_id or previous_download:
        resource.download_count += 1
        db.session.commit()
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            resource.file_path,
            as_attachment=True
        )
    
    # 首次下载需要检查积分
    if current_user.points < resource.points_required:
        flash('积分不足，无法下载')
        return redirect(url_for('resource.detail', id=id))
        
    # 扣除积分并记录
    if current_user.deduct_points(
        resource.points_required,
        f'下载资源《{resource.title}》',
        resource
    ):
        resource.user.add_points(
            resource.points_required,
            f'资源《{resource.title}》被下载',
            resource
        )
        resource.download_count += 1
        # 添加下载记录
        download = Download(user_id=current_user.id, resource_id=resource.id)
        db.session.add(download)
        notify_resource_download(resource, current_user)
        db.session.commit()
    else:
        flash('积分不足，无法下载')
        return redirect(url_for('resource.detail', id=id))
    
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        resource.file_path,
        as_attachment=True
    )

@bp.route('/list')
def list():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    
    query = Resource.query
    if category_id:
        query = query.filter_by(category_id=category_id)
        
    resources = query.order_by(Resource.created_at.desc()).paginate(page=page, per_page=12)
    categories = Category.query.all()
    
    return render_template('resource/list.html', resources=resources, categories=categories)

@bp.route('/<int:id>/comment', methods=['POST'])
@login_required
def comment(id):
    resource = Resource.query.get_or_404(id)
    content = request.form.get('content')
    
    if not content:
        flash('评论内容不能为空')
        return redirect(url_for('resource.detail', id=id))
        
    try:
        comment = Comment(
            content=content,
            user_id=current_user.id,
            resource_id=resource.id
        )
        db.session.add(comment)
        db.session.commit()
        
        # 发送通知
        try:
            notify_resource_comment(resource, comment)
        except Exception as e:
            current_app.logger.error(f'发送评论通知失败: {str(e)}')
            # 通知发送失败不影响评论功能
            
        flash('评论发表成功')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'发表评论失败: {str(e)}')
        flash('评论发表失败，请稍后重试')
        
    return redirect(url_for('resource.detail', id=id)) 

@bp.route('/search')
def search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if query:
        resources = Resource.query.filter(
            or_(
                Resource.title.ilike(f'%{query}%'),
                Resource.description.ilike(f'%{query}%')
            )
        ).order_by(Resource.created_at.desc()).paginate(page=page, per_page=12)
    else:
        resources = Resource.query.order_by(
            Resource.created_at.desc()
        ).paginate(page=page, per_page=12)
    
    return render_template('resource/search.html', 
                         resources=resources, 
                         query=query)

@bp.route('/<int:id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(id):
    resource = Resource.query.get_or_404(id)
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        resource_id=resource.id
    ).first()
    
    if favorite:
        db.session.delete(favorite)
        message = '取消收藏成功'
    else:
        favorite = Favorite(user_id=current_user.id, resource_id=resource.id)
        db.session.add(favorite)
        message = '收藏成功'
    
    db.session.commit()
    flash(message)
    return redirect(url_for('resource.detail', id=id)) 

@bp.route('/comment/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    
    # 检查权限：只有评论作者和管理员可以删除评论
    if comment.user_id != current_user.id and not current_user.is_administrator():
        abort(403)
    
    try:
        db.session.delete(comment)
        db.session.commit()
        flash('评论已删除')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除评论失败: {str(e)}')
        flash('删除评论失败，请稍后重试')
    
    return redirect(url_for('resource.detail', id=comment.resource_id)) 