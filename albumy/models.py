"""
角色与权限：多对多
角色和用户：一对多
用户和图片：一对多
标签和图片：一对多
评论和回复：一对多（自引用）
图片和评论：一对多
用户和评论：一对多
图片和标签：多对多
用户和图片：多对多（收藏功能）
关注功能：用户和用户---多对多
用户和通知：一对多
"""
import os
from datetime import datetime

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_avatars import Identicon

from albumy.extensions import db, whooshee


roles_permissions = db.Table('roles_permissions',
                             db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
                             db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
                             )


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    roles = db.relationship('Role', secondary=roles_permissions, back_populates='permissions', lazy='dynamic')


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    permissions = db.relationship('Permission', secondary=roles_permissions, back_populates='roles', lazy='dynamic')
    users = db.relationship('User', back_populates="role")

    @staticmethod
    def init_role():
        roles_permissions_map = {
            'Locked': ['FOLLOW', 'COLLECT'],
            'User': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD'],
            'Moderator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE'],
            'Administrator': ['FOLLOW', 'COLLECT', 'COMMENT', 'UPLOAD', 'MODERATE', 'ADMINISTER']
        }
        for role_name in roles_permissions_map:
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.session.add(role)
            role.permissions = []
            for permission_name in roles_permissions_map[role_name]:
                permission = Permission.query.filter_by(name=permission_name).first()
                if permission is None:
                    permission = Permission(name=permission_name)
                    db.session.add(permission)
                role.permissions.append(permission)
            db.session.commit()


class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship('User', foreign_keys=[follower_id], back_populates='following', lazy='joined')
    followed = db.relationship('User', foreign_keys=[followed_id], back_populates='followers', lazy='joined')


@whooshee.register_model('name', 'username')
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, index=True)
    email = db.Column(db.String(254), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(30))
    website = db.Column(db.String(255))
    bio = db.Column(db.String(120))
    location = db.Column(db.String(50))
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    avatar_raw = db.Column(db.String(64))

    confirmed = db.Column(db.Boolean, default=False)
    locked = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)

    public_collections = db.Column(db.Boolean, default=True)
    receive_collect_notification = db.Column(db.Boolean, default=True)
    receive_comment_notification = db.Column(db.Boolean, default=True)
    receive_follow_notification = db.Column(db.Boolean, default=True)

    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', back_populates='users')

    photos = db.relationship('Photo', back_populates='author', cascade='all')
    comments = db.relationship('Comment', back_populates='author', cascade='all')
    collections = db.relationship('Collect', back_populates='collector', cascade='all')
    following = db.relationship('Follow', back_populates='follower', foreign_keys=[Follow.follower_id], lazy='dynamic',
                                cascade='all')
    followers = db.relationship('Follow', back_populates='followed', foreign_keys=[Follow.followed_id], lazy='dynamic',
                                cascade='all')
    notifications = db.relationship('Notification', back_populates='receiver', cascade='all')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_role()
        self.generate_avatar()
        self.follow(self)

    def set_role(self):
        if self.role is None:
            if self.email == current_app.config['ALBUMY_ADMIN_EMAIL']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(name='User').first()
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute.')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role.name == 'Administrator'

    def can(self, permission_name):
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role is not None and permission in self.role.permissions

    def generate_avatar(self):
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        db.session.commit()

    def is_collecting(self, photo):
        return Collect.query.with_parent(self).filter_by(collected_id=photo.id).first() is not None

    def collect(self, photo):
        if not self.is_collecting(photo):
            collect = Collect(collector=self, collected=photo)
            db.session.add(collect)
            db.session.commit()

    def un_collect(self, photo):
        collect = Collect.query.with_parent(self).filter_by(collected_id=photo.id).first()
        if collect:
            db.session.delete(collect)
            db.session.commit()

    def is_following(self, user):
        if user.id is None:  # 为了在构造方法中关注自己，因为在未提交数据库时，user对象尚未获得id
            return False
        return self.following.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def un_follow(self, user):
        follow = self.following.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def lock(self):
        self.locked = True
        self.role = Role.query.filter_by(name='Locked').first()
        db.session.commit()

    def unlock(self):
        self.locked = False
        self.role = Role.query.filter_by(name='User').first()
        db.session.commit()

    def block(self):
        self.active = False
        db.session.commit()

    def unblock(self):
        self.active = True
        db.session.commit()

    @property
    def is_active(self):
        return self.active



class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    receiver = db.relationship('User', back_populates='notifications')


class Collect(db.Model):
    collector_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    collected_id = db.Column(db.Integer, db.ForeignKey('photo.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # 使用关系表时，可以直接加载关系的另一侧；使用关系模型时，必须指定joined，才能一次性加载关系的另一侧
    collected = db.relationship('Photo', back_populates='collectors', lazy='joined')
    collector = db.relationship('User', back_populates='collections', lazy='joined')


tagging = db.Table('tagging',
                   db.Column('photo_id', db.Integer, db.ForeignKey('photo.id')),
                   db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')))

@whooshee.register_model('description')
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64))
    filename = db.Column(db.String(64))
    filename_s = db.Column(db.String(64))
    filename_m = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    can_comment = db.Column(db.Boolean, default=True)
    # 存储被举报的次数
    flag = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    author = db.relationship('User', back_populates='photos')
    tags = db.relationship('Tag', secondary=tagging, back_populates='photos')
    comments = db.relationship('Comment', back_populates='photo', cascade='all')
    collectors = db.relationship('Collect', back_populates='collected', cascade='all')


@whooshee.register_model('name')
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)

    photos = db.relationship('Photo', secondary=tagging, back_populates='tags')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # 存储被举报的次数
    flag = db.Column(db.Integer, default=0)

    replied_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    replies = db.relationship('Comment', back_populates='replied', cascade='all')
    # 自引用一对多，使用remote_id指定一这一侧的关系，并且指定值唯一的字段；
    replied = db.relationship('Comment', back_populates='replies', remote_side=[id])

    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'))
    photo = db.relationship('Photo', back_populates='comments')

    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', back_populates='comments')


@db.event.listens_for(Photo, 'after_delete', named=True)
def delete_photos(**kwargs):
    """某张照片被移除时，自动删除目录下的文件"""
    target = kwargs['target']
    for filename in [target.filename, target.filename_s, target.filename_m]:
        path = os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename)
        if os.path.exists(path):
            os.remove(path)


@db.event.listens_for(User, 'after_delete', named=True)
def delete_avatars(**kwargs):
    """用户注销时，删除用户头像"""
    target = kwargs.get('target')
    for filename in [target.avatar_s, target.avatar_m, target.avatar_l, target.avatar_raw]:
        if filename is not None:  # avatar_raw may be none
            path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], filename)
            if os.path.exists(path):  # not every filename map a unique file
                os.remove(path)


@db.event.listens_for(User.avatar_s, 'set', named=True)
def change_avatars(**kwargs):
    oldvalue = kwargs.get('oldvalue')
    if oldvalue:
        prefix = oldvalue.split('_')[0]
        suffix = oldvalue.split('.')[-1]
        for filename in [oldvalue, prefix + '_m.' + suffix, prefix + '_l.' + suffix]:
            if filename is not None:
                path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], filename)
                if os.path.exists(path):
                    os.remove(path)


@db.event.listens_for(User.avatar_raw, 'set', named=True)
def change_avatar_raw(**kwargs):
    oldvalue = kwargs.get('oldvalue')
    if oldvalue is not None:
        path = os.path.join(current_app.config['AVATARS_SAVE_PATH'], oldvalue)
        if os.path.exists(path):
            os.remove(path)


