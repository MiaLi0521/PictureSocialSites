from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, HiddenField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, Regexp

from albumy.models import User


class EditProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(1, 30)])
    username = StringField('Username',
                           validators=[DataRequired(), Length(1, 20),
                                       Regexp('^[a-zA-Z0-9]*$',
                                              message='The username should contain only a-z, A-Z and 0-9.')])
    website = StringField('Website', validators=[Optional(), Length(0, 255)])
    location = StringField('City', validators=[Optional(), Length(0, 50)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(0, 120)])
    submit = SubmitField()

    def validate_username(self, filed):
        if filed.data != current_user.username and User.query.filter_by(username=filed.data).first():
            raise ValidationError('The username is already in use.')


class UploadAvatarForm(FlaskForm):
    image = FileField('Upload Avatar', validators=[
        FileRequired(), FileAllowed(['jpg', 'png'], 'The file format should be .jpg or .png.')])
    submit = SubmitField()


class CropAvatarForm(FlaskForm):
    x = HiddenField()
    y = HiddenField()
    w = HiddenField()
    h = HiddenField()
    submit = SubmitField('Crop and Update')


class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()

    def validate_email(self, field):
        if current_user.email == field.data.lower():
            raise ValidationError('Email is same as current email in use.')


class ChangePasswordForm(FlaskForm):
    oldpassword = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[DataRequired(), Length(8, 128),
                                                         EqualTo('password2')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField()

    def validate_oldpassword(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError('Old password verify failed.')


class NotificationForm(FlaskForm):
    receive_comment_notification = BooleanField('New Comment')
    receive_follow_notification = BooleanField('New Follow')
    receive_collect_notification = BooleanField('New collector')
    submit = SubmitField()


class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField('Public my collection')
    submit = SubmitField()


class DeleteAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 20)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username:
            raise ValidationError('Wrong username.s')







