from flask import Blueprint, render_template, request
from app.models.resource import Resource
from app.models.category import Category
from app.models.user import User
from sqlalchemy import func, or_, and_
from app import db
from flask_login import current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '')
    
    # 构建基础查询
    if current_user.is_authenticated:
        if current_user.is_administrator():
            # 管理员可以看到所有资源
            query = Resource.query
        else:
            # 普通用户只能看到已通过审核的资源和自己上传的资源
            query = Resource.query.filter(
                or_(
                    Resource.status == 'approved',
                    and_(
                        Resource.user_id == current_user.id,
                        Resource.status != 'approved'
                    )
                )
            )
    else:
        # 未登录用户只能看到已通过审核的资源
        query = Resource.query.filter(Resource.status == 'approved')
    
    # 应用分类过滤
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # 应用搜索过滤
    if search:
        query = query.filter(
            or_(
                Resource.title.ilike(f'%{search}%'),
                Resource.description.ilike(f'%{search}%')
            )
        )
    
    # 按创建时间倒序排序并分页
    resources = query.order_by(Resource.created_at.desc()).paginate()
    
    return render_template('main/index.html',
                         resources=resources,
                         categories=Category.query.all(),
                         current_category_id=category_id,
                         search=search) 