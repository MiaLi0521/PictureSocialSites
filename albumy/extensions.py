from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import CSRFProtect
from flask_login import LoginManager, AnonymousUserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
from flask_mail import Mail
from flask_migrate import Migrate
from flask_dropzone import Dropzone
from flask_avatars import Avatars

bootstrap = Bootstrap()
moment = Moment()
CSRFProtect = CSRFProtect()
mail = Mail()
login_manager = LoginManager()
db = SQLAlchemy()
whooshee = Whooshee()
migrate = Migrate()
dropzone = Dropzone()
avatars = Avatars()


@login_manager.user_loader
def load_user(user_id):
    from albumy.models import User
    user = User.query.get(int(user_id))
    return user


class AnonymousUser(AnonymousUserMixin):
    """Flask-login提供的current_user是当前用户的代理对象，我们经常借助它来调用User类的方法和属性；但是当用户未登录时，current_user
    指向的用户对象是Flask-Login提供的匿名用户类AnonymousUserMixin"""
    @property
    def is_admin(self):
        return False

    def can(self, permission_name):
        return False


login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
login_manager.anonymous_user = AnonymousUser




