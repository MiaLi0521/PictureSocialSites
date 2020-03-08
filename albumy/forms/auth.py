"""
用户登录
用户注册
忘记密码
密码重置
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, URL, Length, Regexp, EqualTo, ValidationError

from albumy.models import User


class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    remember = BooleanField('remember me')
    submit = SubmitField('Log in')


class RegisterForm(FlaskForm):
    name = StringField('name', validators=[DataRequired(), Length(1, 30)])
    email = StringField('email', validators=[DataRequired(), Length(1, 254), Email()])
    username = StringField('username', validators=[
        DataRequired(), Length(1, 20),
        Regexp('^[a-zA-Z0-9]*$', message='The username should contain only a-z, A-Z and 0-9.')])
    password = PasswordField('password', validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('the email is already in use.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('the username is already in use.')


class ForgetPasswordForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()


class ResetPasswordForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField('new password', validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('confirm password', validators=[DataRequired()])
    submit = SubmitField('reset password')















