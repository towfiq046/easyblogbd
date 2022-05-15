from flask_babel import lazy_gettext as _l
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, Length, EqualTo, Optional

from app.constants import USERNAME_LENGTH, PASSWORD_LENGTH, ABOUT_ME_LENGTH, POST_LENGTH, USERNAME_REQUIRED_STRING, \
    USERNAME_LENGTH_STRING, EMAIL_REQUIRED_STRING, PASSWORD_LENGTH_STRING, PASSWORD_REQUIRED_STRING, \
    PASSWORD_MATCH_STRING
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
    email = StringField(label=_l('Email'), validators=[DataRequired(message=EMAIL_REQUIRED_STRING), Email()])
    password = PasswordField(label=_l('New Password'), validators=[DataRequired(message=PASSWORD_REQUIRED_STRING),
                                                                   Length(min=6, max=PASSWORD_LENGTH,
                                                                          message=PASSWORD_LENGTH_STRING)])
    confirm = PasswordField(label=_l('Repeat Password'),
                            validators=[EqualTo('password', message=PASSWORD_MATCH_STRING)])
    submit = SubmitField(label=_l('Register'))

    @staticmethod
    def validate_username(self, username):
        _validate_username(username)

    @staticmethod
    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email is not None:
            raise ValidationError(_l('This email is taken, please use a different email.'))


class EditProfileForm(FlaskForm):
    username = StringField(label=_l('Username'), validators=[DataRequired(message=USERNAME_REQUIRED_STRING),
                                                             Length(min=3, max=USERNAME_LENGTH,
                                                                    message=USERNAME_LENGTH_STRING)])
    about_me = TextAreaField(label=_l('About me'), validators=[Optional(), Length(max=ABOUT_ME_LENGTH)],
                             render_kw={'cols': 50, 'row': 4})
    submit = SubmitField(label=_l('Submit'))

    @staticmethod
    def validate_username(self, username):
        _validate_username(username)


class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))


class PostForm(FlaskForm):
    post = TextAreaField(label="", validators=[DataRequired(message=_l('Please write something.')),
                                               Length(min=1, max=POST_LENGTH, message=_l(
                                                   'Post must be between %(min)d to %(max)d characters.'))],
                         render_kw={'placeholder': _l("What's on your mind")})
    submit = SubmitField(_l('Post'))


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


def _validate_username(username):
    user = User.query.filter_by(username=username.data).first()
    if user and user != current_user:
        raise ValidationError(_l('This username is taken, please use a different username.'))
