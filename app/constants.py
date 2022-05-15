from flask_babel import lazy_gettext as _l

USERNAME_LENGTH = 64
EMAIL_LENGTH = 80
PASSWORD_LENGTH = 128
ABOUT_ME_LENGTH = 200
POST_LENGTH = 1200

USERNAME_REQUIRED_STRING = _l('Please enter your username.')
USERNAME_LENGTH_STRING = _l('Username must be between %(min)d to %(max)d characters.')
EMAIL_REQUIRED_STRING = _l('Please enter your email.')
PASSWORD_REQUIRED_STRING = _l('Please enter a strong password.')
PASSWORD_LENGTH_STRING = _l('Password must be between %(min)d to %(max)d characters.')
PASSWORD_MATCH_STRING = _l('Passwords must match.')
