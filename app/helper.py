from flask import flash, redirect, url_for
from flask_babel import lazy_gettext as _l
from flask_login import current_user
from wtforms import ValidationError

from app.models import User


def validate_username(username):
    user = User.query.filter_by(username=username.data).first()
    if user and user != current_user:
        raise ValidationError(_l('This username is taken, please use a different username.'))


def flash_message_and_redirect(*, message: str, endpoint: str, category: str = '', username: str = None):
    flash(message, category)
    if endpoint == 'main.profile':
        return redirect(url_for(endpoint, username=username))
    return redirect(url_for(endpoint))

