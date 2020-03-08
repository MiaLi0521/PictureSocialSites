import os
import random

from faker import Faker
from sqlalchemy.exc import IntegrityError
from PIL import Image
from flask import current_app

from albumy.models import User, Photo, Tag, Comment, Notification
from albumy.extensions import db

fake = Faker()


def fake_admin():
    admin = User(name='Mia Li', username='miali', email='2689518718@qq.com',
                 bio=fake.sentence(), website='http://miali.com', confirmed=True)
    admin.password = 'admin'
    admin.notifications.append(Notification(message='Hello, welcome to Albumy.'))
    db.session.add(admin)
    db.session.commit()


def fake_user(count=10):
    for i in range(count):
        user = User(name=fake.name(),
                    username=fake.user_name(),
                    confirmed=True,
                    bio=fake.sentence(),
                    location=fake.city(),
                    website=fake.url(),
                    member_since=fake.date_this_decade(),
                    email=fake.email())
        user.password = '123456'
        user.notifications.append(Notification(message='Hello, welcome to Albumy.'))
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_follow(count=30):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.follow(User.query.get(random.randint(1, User.query.count())))


def fake_tag(count=20):
    for i in range(count):
        tag = Tag(name=fake.word())
        db.session.add(tag)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def fake_photo(count=30):
    upload_path = current_app.config['ALBUMY_UPLOAD_PATH']
    for i in range(count):
        filename = 'random_%d.jpg' % i
        r = lambda: random.randint(128, 255)
        image = Image.new(mode='RGB', size=(800, 800), color=(r(), r(), r()))
        image.save(os.path.join(upload_path, filename))

        photo = Photo(
            description=fake.text(),
            filename=filename,
            filename_m=filename,
            filename_s=filename,
            author=User.query.get(random.randint(1, User.query.count())),
            timestamp=fake.date_time_this_year()
        )

        for i in range(random.randint(1, 5)):
            tag = Tag.query.get(random.randint(1, Tag.query.count()))
            if tag not in photo.tags:
                photo.tags.append(tag)

        db.session.add(photo)
    db.session.commit()


def fake_comment(count=100):
    for i in range(count):
        comment = Comment(
            author=User.query.get(random.randint(1, User.query.count())),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            photo=Photo.query.get(random.randint(1, Photo.query.count()))
        )
        db.session.add(comment)
    db.session.commit()

    # 产生200条回复
    for j in range(count * 2):
        comment = Comment.query.get(random.randint(1, Comment.query.count()))
        reply = Comment(
            author=User.query.get(random.randint(1, User.query.count())),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year(),
            photo=comment.photo,
            replied=comment
        )
        db.session.add(reply)
    db.session.commit()


def fake_collect(count=50):
    for i in range(count):
        user = User.query.get(random.randint(1, User.query.count()))
        user.collect(Photo.query.get(random.randint(1, Photo.query.count())))
    db.session.commit()

