import os

from flask import Flask, render_template
import click
from flask_login import current_user

from albumy.settings import config
from albumy.extensions import bootstrap, db, moment, CSRFProtect, mail, login_manager, whooshee, mail, migrate, \
    dropzone, avatars
from albumy.blueprints.admin import admin_bp
from albumy.blueprints.ajax import ajax_bp
from albumy.blueprints.auth import auth_bp
from albumy.blueprints.main import main_bp
from albumy.blueprints.user import user_bp
from albumy.models import User, Role, Permission, roles_permissions, Photo, Tag, Follow, Collect, Comment, Notification


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')
    app = Flask('albumy')
    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_shell_context(app)
    register_template_context(app)
    register_errorhandlers(app)
    register_commands(app)

    return app


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    CSRFProtect.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    whooshee.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    dropzone.init_app(app)
    avatars.init_app(app)


def register_blueprints(app):
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(ajax_bp, url_prefix='/ajax')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp, url_prefix='/user')


def register_shell_context(app):
    @app.shell_context_processor
    def make_shell_context():
        return dict(db=db, User=User, Photo=Photo, Tag=Tag, Follow=Follow, Collect=Collect, Comment=Comment)


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if current_user.is_authenticated:
            notification_count = Notification.query.with_parent(current_user).filter_by(is_read=False).count()
        else:
            notification_count = None
        return dict(notification_count=notification_count)


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop')
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized the database.')

    @app.cli.command()
    def init():
        """Initialize the Albumy"""
        click.echo('Initialize the database...')
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()

        click.echo('Done')

    @app.cli.command()
    def reindex():
        click.echo('whooshee reindex...')
        whooshee.reindex()

    @app.cli.command()
    @click.option('--user', default=50, help='Quantity of users, default is 10.')
    @click.option('--tag', default=20, help='Quantity of tags, default is 20.')
    @click.option('--photo', default=30, help='Quantity of photos, default is 30.')
    @click.option('--comment', default=100, help='Quantity of comments, default is 100.')
    @click.option('--collect', default=300, help='Quantity of collects, default is 300.')
    @click.option('--follow', default=100, help='Quantity of follows, default is 30.')
    def forge(user, photo, tag, comment, collect, follow):
        """Generate fake data."""
        from albumy.fakes import fake_user, fake_admin, fake_tag, fake_photo, fake_comment, fake_collect, fake_follow
        from flask import current_app

        uploads_path = current_app.config['ALBUMY_UPLOAD_PATH']
        avatars_path = current_app.config['AVATARS_SAVE_PATH']

        for f in os.listdir(uploads_path):
            filepath = os.path.join(uploads_path, f)
            if os.path.isfile(filepath):
                os.remove(filepath)
                print('delete uploads file {}'.format(f))

        for f in os.listdir(avatars_path):
            filepath = os.path.join(avatars_path, f)
            if os.path.isfile(filepath):
                os.remove(filepath)
                print('delete uploads file {}'.format(f))

        click.echo('drop tables and then create...')
        db.drop_all()
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()

        click.echo('Generating the administrator...')
        fake_admin()
        click.echo('Generating %d users...' % user)
        fake_user(user)
        click.echo('Generating %d tags...' % tag)
        fake_tag()
        click.echo('Generating %d photos...' % photo)
        fake_photo(photo)
        click.echo('Generating %d comments...' % comment)
        fake_comment(comment)
        click.echo('Generating %d collects...' % collect)
        fake_collect(collect)
        click.echo('Generating %d follows...' % follow)
        fake_follow(follow)

        click.echo('Done.')
















