import os
import sys

base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

if sys.platform.startswith('win'):
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class Operations:
    CONFIRM = 'confirm'
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'


class BaseConfig:
    ALBUMY_ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@helloflask.com')
    ALBUMY_MAIL_SUBJECT_PREFIX = '[Albumy]'
    ALBUMY_PHOTO_PER_PAGE = 12
    ALBUMY_COMMENT_PER_PAGE = 15
    ALBUMY_NOTIFICATION_PER_PAGE = 20
    ALBUMY_USER_PER_PAGE = 20
    ALBUMY_MANAGE_PHOTO_PER_PAGE = 20
    ALBUMY_MANAGE_USER_PER_PAGE = 30
    ALBUMY_MANAGE_TAG_PER_PAGE = 50
    ALBUMY_MANAGE_COMMENT_PER_PAGE = 30
    ALBUMY_SEARCH_RESULT_PER_PAGE = 20
    ALBUMY_UPLOAD_PATH = os.path.join(base_dir, 'uploads')
    ALBUMY_PHOTO_SIZE = {'small': 400, 'medium': 800}
    ALBUMY_PHOTO_SUFFIX = {
        ALBUMY_PHOTO_SIZE['small']: '_s',  # thumbnail
        ALBUMY_PHOTO_SIZE['medium']: '_m',  # display
    }

    SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')
    MAX_CONTENT_LENGTH  = 3 * 1024 * 1024  # 上传文件大小超过3M，返回413错误

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Albumy admin', MAIL_USERNAME)
    MAIL_PORT = 465
    MAIL_USE_SSL = True

    DROPZONE_ALLOWED_FILE_TYPE = 'image'
    DROPZONE_MAX_FILE_SIZE = 3
    DROPZONE_MAX_FILES = 30
    DROPZONE_ENABLE_CSRF = True

    AVATARS_SAVE_PATH = os.path.join(ALBUMY_UPLOAD_PATH, 'avatars')
    # 设置3种尺寸的头像图片大小
    AVATARS_SIZE_TUPLE = (30, 100, 200)

    WHOOSHEE_MIN_STRING_LEN = 1


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = prefix + os.path.join(base_dir, 'data-dev.db')


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLE = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = prefix + os.path.join(base_dir, 'data.db')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
