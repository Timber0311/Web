from app.models.notification import Notification
from app import db
from flask import current_app
import re

def send_notification(user_id, title, content):
    """
    发送通知
    :param user_id: 接收通知的用户ID
    :param title: 通知标题
    :param content: 通知内容
    """
    notification = Notification(
        user_id=user_id,
        title=title,
        content=content
    )
    db.session.add(notification)
    db.session.commit()

def extract_mentions(content):
    """
    从评论内容中提取@用户名
    返回提到的用户名列表
    """
    # 匹配@后面的用户名，用户名可以包含字母、数字、下划线
    pattern = r'@([a-zA-Z0-9_]+)'
    return re.findall(pattern, content)

def notify_resource_comment(resource, comment):
    """
    当资源收到评论时通知资源上传者
    """
    # 检查必要的关联是否存在
    if not resource or not comment or not comment.user or not resource.user:
        current_app.logger.error('通知发送失败：缺少必要的用户或资源信息')
        return
    
    # 如果评论者不是资源上传者自己，则发送通知
    if resource.user_id != comment.user_id:
        title = f'您的资源"{resource.title}"收到了新评论'
        content = f'{comment.user.username}评论道：{comment.content}'
        send_notification(resource.user_id, title, content)

def notify_resource_download(resource, user):
    """
    当资源被下载时通知资源上传者
    """
    if resource.user_id != user.id:
        title = f'您的资源"{resource.title}"被下载了'
        content = f'{user.username}下载了您的资源，您获得了{resource.points_required}积分'
        send_notification(resource.user_id, title, content)

def notify_resource_approved(resource):
    """
    当资源审核通过时通知上传者
    """
    title = f'您的资源"{resource.title}"已通过审核'
    content = '您上传的资源已通过审核，现在其他用户可以下载了。'
    send_notification(resource.user_id, title, content)

def notify_resource_rejected(resource):
    """
    当资源被拒绝时通知上传者
    """
    title = f'您的资源"{resource.title}"未通过审核'
    content = f'您上传的资源未通过审核。原因：{resource.reject_reason or "无"}'
    send_notification(resource.user_id, title, content)

def notify_resource_review_approved(resource):
    """
    当资源复核通过时通知上传者
    """
    title = f'您的资源"{resource.title}"已通过复核'
    content = '您的资源已通过复核，现在其他用户可以下载了。'
    send_notification(resource.user_id, title, content)

def notify_resource_review_rejected(resource):
    """
    当资源复核被拒绝时通知上传者
    """
    title = f'您的资源"{resource.title}"未通过复核'
    content = f'您的资源未通过复核。原因：{resource.reject_reason or "无"}'
    send_notification(resource.user_id, title, content) 