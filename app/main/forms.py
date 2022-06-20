from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.constants import USERNAME_LENGTH, ABOUT_ME_LENGTH, POST_LENGTH, USERNAME_REQUIRED_STRING, \
    USERNAME_LENGTH_STRING
from app.helper import validate_username


class EditProfileForm(FlaskForm):
    username = StringField(label=_l('Username'), validators=[DataRequired(message=USERNAME_REQUIRED_STRING),
                                                             Length(min=3, max=USERNAME_LENGTH,
                                                                    message=USERNAME_LENGTH_STRING)])
    about_me = TextAreaField(label=_l('About me'), validators=[Optional(), Length(max=ABOUT_ME_LENGTH)],
                             render_kw={'cols': 50, 'row': 4})
    submit = SubmitField(label=_l('Submit'))

    @staticmethod
    def validate_username(self, username):
        validate_username(username)


class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))


class PostForm(FlaskForm):
    post = TextAreaField(label="", validators=[DataRequired(message=_l('Please write something.')),
                                               Length(min=1, max=POST_LENGTH, message=_l(
                                                   'Post must be between %(min)d to %(max)d characters.'))],
                         render_kw={'placeholder': _l("What's on your mind")})
    submit = SubmitField(_l('Post'))
