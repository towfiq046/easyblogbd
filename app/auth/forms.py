from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Email

from app.constants import (USERNAME_REQUIRED_MESSAGE, USERNAME_LENGTH, USERNAME_LENGTH_MESSAGE, EMAIL_REQUIRED_MESSAGE,
                           PASSWORD_REQUIRED_MESSAGE, PASSWORD_LENGTH, PASSWORD_LENGTH_MESSAGE, PASSWORD_MATCH_MESSAGE)
from app.helper import validate_username
from app.models import User


class LoginForm(FlaskForm):
    username = StringField(label=lazy_gettext('Username'), validators=[DataRequired(message=USERNAME_REQUIRED_MESSAGE)])
    password = PasswordField(
        label=lazy_gettext('Password'),
        validators=[DataRequired(message=lazy_gettext('Please enter your password.'))])
    remember_me = BooleanField(label=lazy_gettext('Remember Me'))
    submit = SubmitField(label=lazy_gettext('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(
        label=lazy_gettext('Username'),
        validators=[
            DataRequired(message=USERNAME_REQUIRED_MESSAGE),
            Length(min=3, max=USERNAME_LENGTH, message=USERNAME_LENGTH_MESSAGE)],
        render_kw={})
    email = StringField(
        label=lazy_gettext('Email'),
        validators=[
            DataRequired(message=EMAIL_REQUIRED_MESSAGE),
            Email(message=lazy_gettext('Please enter a valid email address.'))])
    password = PasswordField(
        label=lazy_gettext('New Password'),
        validators=[
            DataRequired(message=PASSWORD_REQUIRED_MESSAGE),
            Length(min=6, max=PASSWORD_LENGTH, message=PASSWORD_LENGTH_MESSAGE)])
    confirm = PasswordField(
        label=lazy_gettext('Repeat Password'),
        validators=[EqualTo('password', message=PASSWORD_MATCH_MESSAGE)])
    submit = SubmitField(label=lazy_gettext('Register'))

    def validate_username(self, username):
        validate_username(username)

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email is not None:
            raise ValidationError(lazy_gettext('This email is taken, please use a different email.'))


class ResetPasswordRequestForm(FlaskForm):
    username = StringField(label=lazy_gettext('Username'), validators=[DataRequired(message=USERNAME_REQUIRED_MESSAGE)])
    email = StringField(label=lazy_gettext('Email'), validators=[DataRequired(message=EMAIL_REQUIRED_MESSAGE), Email()])
    submit = SubmitField(lazy_gettext('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        label=lazy_gettext('New Password'),
        validators=[
            DataRequired(message=PASSWORD_REQUIRED_MESSAGE),
            Length(min=6, max=PASSWORD_LENGTH, message=PASSWORD_LENGTH_MESSAGE)])
    confirm = PasswordField(
        label=lazy_gettext('Repeat Password'),
        validators=[EqualTo('password', message=PASSWORD_MATCH_MESSAGE)])
    submit = SubmitField(lazy_gettext('Reset Password'))
