from flask_babel import lazy_gettext

ABOUT_ME_LENGTH = 200
EMAIL_LENGTH = 80
MESSAGE_LENGTH = 500
NAME_LENGTH = 128
PASSWORD_LENGTH = 128
POST_LENGTH = 1200
USERNAME_LENGTH = 64

ABOUT_ME_MESSAGE = lazy_gettext('About me can not exceed 200 characters.')
EMAIL_REQUIRED_MESSAGE = lazy_gettext('Please enter your email.')
PASSWORD_LENGTH_MESSAGE = lazy_gettext('Password must be between %(min)d to %(max)d characters.')
PASSWORD_MATCH_MESSAGE = lazy_gettext('Passwords must match.')
PASSWORD_REQUIRED_MESSAGE = lazy_gettext('Please enter a strong password.')
USERNAME_LENGTH_MESSAGE = lazy_gettext('Username must be between %(min)d to %(max)d characters.')
USERNAME_REQUIRED_MESSAGE = lazy_gettext('Please enter your username.')
WRITE_SOMETHING_MESSAGE = lazy_gettext('Please write something.')
