from flask import Blueprint, render_template, jsonify
from flask_login import current_user

from albumy.models import User, Notification, Photo
from albumy.notifications import push_collect_notification

ajax_bp = Blueprint('ajax', __name__)


@ajax_bp.route('/profile/<int:user_id>')
def get_profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('main/profile_popup.html', user=user)


@ajax_bp.route('/followers-count/<int:user_id>')
def followers_count(user_id):
    user = User.query.get_or_404(user_id)
    count = user.followers.count() - 1
    return jsonify(count=count)


@ajax_bp.route('/follow/<username>', methods=['POST'])
def follow(username):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403
    if not current_user.confirmed:
        return jsonify(message='Confirm account required.'), 400
    if not current_user.can('FOLLOW'):
        return jsonify(message='No permission.'), 403
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        return jsonify(message='Already followed.'), 400
    current_user.follow(user)
    return jsonify(message='User followed.')


@ajax_bp.route('/un-follow/<username>', methods=['POST'])
def un_follow(username):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403

    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        return jsonify(message='Not follow yet.'), 400

    current_user.un_follow(user)
    return jsonify(message='Follow canceled.')


@ajax_bp.route('/notifications-count')
def notifications_count():
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403
    count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
    return jsonify(count=count)


@ajax_bp.route('/<int:photo_id>/collectors_count')
def collectors_count(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    count = len(photo.collectors)
    return jsonify(count=count)


@ajax_bp.route('/collect/<int:photo_id>', methods=['POST'])
def collect(photo_id):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403
    if not current_user.confirmed:
        return jsonify(message='Confirm account required.'), 400
    if not current_user.can('COLLECT'):
        return jsonify(message='No Permission.'), 403

    photo = Photo.query.get_or_404(photo_id)
    if current_user.is_collecting(photo):
        return jsonify(message='Already collected.'), 400

    current_user.collect(photo)
    if current_user != photo.author and photo.author.receive_collect_notification:
        push_collect_notification(collector=current_user, photo_id=photo_id, receiver=photo.author)

    return jsonify(message='Photo collected.')


@ajax_bp.route('/uncollect/<int:photo_id>', methods=['POST'])
def un_collect(photo_id):
    if not current_user.is_authenticated:
        return jsonify(message='Login required.'), 403

    photo = Photo.query.get_or_404(photo_id)
    if not current_user.is_collecting(photo):
        return jsonify(message='Not collect yet.'), 400

    current_user.un_collect(photo)
    return jsonify(message='Collect canceled.')

