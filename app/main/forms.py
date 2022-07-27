from flask import request
from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.constants import (USERNAME_LENGTH, ABOUT_ME_LENGTH, POST_LENGTH, USERNAME_REQUIRED_MESSAGE,
                           USERNAME_LENGTH_MESSAGE, ABOUT_ME_MESSAGE)
from app.helper import validate_username


class EditProfileForm(FlaskForm):
    username = StringField(
        label=lazy_gettext('Username'),
        validators=[
            DataRequired(message=USERNAME_REQUIRED_MESSAGE),
            Length(min=3, max=USERNAME_LENGTH, message=USERNAME_LENGTH_MESSAGE)])
    about_me = TextAreaField(
        label=lazy_gettext('About me'),
        validators=[Optional(), Length(max=ABOUT_ME_LENGTH, message=ABOUT_ME_MESSAGE)],
        render_kw={'cols': 50, 'row': 4})
    submit = SubmitField(label=lazy_gettext('Submit'))

    def validate_username(self, username):
        validate_username(username)


class EmptyForm(FlaskForm):
    submit = SubmitField(lazy_gettext('Submit'))


class PostForm(FlaskForm):
    post = TextAreaField(
        label=lazy_gettext("What's on your mind"),
        validators=[
            DataRequired(message=lazy_gettext('Please write something.')),
            Length(min=1, max=POST_LENGTH,
                   message=lazy_gettext('Post must be between %(min)d to %(max)d characters.'))],
        render_kw={'style': 'height: 100px'})
    submit = SubmitField(lazy_gettext('Post'))


class SearchForm(FlaskForm):
    q = StringField(validators=[DataRequired()], render_kw={'placeholder': lazy_gettext('Search')})

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'meta' not in kwargs:
            kwargs['meta'] = {'csrf': False}
        super(SearchForm, self).__init__(*args, **kwargs)
