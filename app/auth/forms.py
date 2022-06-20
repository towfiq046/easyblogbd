from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Email

from app.constants import USERNAME_REQUIRED_STRING, USERNAME_LENGTH, USERNAME_LENGTH_STRING, EMAIL_REQUIRED_STRING, \
    PASSWORD_REQUIRED_STRING, PASSWORD_LENGTH, PASSWORD_LENGTH_STRING, PASSWORD_MATCH_STRING
from app.helper import validate_username
from app.models import User


class LoginForm(FlaskForm):
    username = StringField(label=_l('Username'), validators=[DataRequired(message=USERNAME_REQUIRED_STRING)])
    password = PasswordField(label=_l('Password'), validators=[DataRequired(message=_l('Please enter your password.'))])
    remember_me = BooleanField(label=_l('Remember Me'))
    submit = SubmitField(label=_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(label=_l('Username'), validators=[DataRequired(message=USERNAME_REQUIRED_STRING),
                                                             Length(min=3, max=USERNAME_LENGTH,
                                                                    message=USERNAME_LENGTH_STRING)],
                           render_kw={})
    email = StringField(label=_l('Email'), validators=[DataRequired(message=EMAIL_REQUIRED_STRING),
                                                       Email(message=_l('Please enter a valid email address.'))])
    password = PasswordField(label=_l('New Password'), validators=[DataRequired(message=PASSWORD_REQUIRED_STRING),
                                                                   Length(min=6, max=PASSWORD_LENGTH,
                                                                          message=PASSWORD_LENGTH_STRING)])
    confirm = PasswordField(label=_l('Repeat Password'),
                            validators=[EqualTo('password', message=PASSWORD_MATCH_STRING)])
    submit = SubmitField(label=_l('Register'))

    @staticmethod
    def validate_username(self, username):
        validate_username(username)

    @staticmethod
    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email is not None:
            raise ValidationError(_l('This email is taken, please use a different email.'))


class ResetPasswordRequestForm(FlaskForm):
    username = StringField(label=_l('Username'), validators=[DataRequired(message=USERNAME_REQUIRED_STRING)])
    email = StringField(label=_l('Email'), validators=[DataRequired(message=EMAIL_REQUIRED_STRING), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(label=_l('New Password'), validators=[DataRequired(message=PASSWORD_REQUIRED_STRING),
                                                                   Length(min=6, max=PASSWORD_LENGTH,
                                                                          message=PASSWORD_LENGTH_STRING)])
    confirm = PasswordField(label=_l('Repeat Password'),
                            validators=[EqualTo('password', message=PASSWORD_MATCH_STRING)])
    submit = SubmitField(_l('Reset Password'))
