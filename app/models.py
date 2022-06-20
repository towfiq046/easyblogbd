from datetime import datetime
from hashlib import md5
from time import time

import jwt
from flask import current_app
from flask_login import UserMixin
from jwt import DecodeError, ExpiredSignatureError
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login
from app.constants import USERNAME_LENGTH, EMAIL_LENGTH, PASSWORD_LENGTH, ABOUT_ME_LENGTH

followers = db.Table('followers', db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))


class User(UserMixin, db.Model):
    """ Model for representing the user table """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(USERNAME_LENGTH), index=True, unique=True)
    email = db.Column(db.String(EMAIL_LENGTH), index=True, unique=True)
    password_hash = db.Column(db.String(PASSWORD_LENGTH))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(ABOUT_ME_LENGTH))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User',
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic')

    def set_password(self, password):
        """
        Sets generated password hash to password_hash class attribute.
        @param password: String
        @return: None
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Checks password against the password hash.
        @param password: String
        @return: Boolean
        """
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        """
        Returns an avatar link as string.
        @param size: Integer
        @return: String
        """
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=retro&s={size}'

    def follow(self, user):
        """
        Appends user to followed list.
        @param user: User
        @return: None
        """
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """
        Removes user from followed list.
        @param user: User
        @return: None
        """
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        """
        Checks if left side user is following given right side user. !!
        @param user: User
        @return: Boolean
        """
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        """
        Query all the followed posts of the user.
        @return: Query!
        """
        followed = Post.query \
            .join(followers, (followers.c.followed_id == Post.user_id)) \
            .filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in}, current_app.config['SECRET_KEY'],
                          algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except (DecodeError, ExpiredSignatureError):
            return
        return User.query.get(id)

    def __repr__(self):
        """
        String representation of User class.
        @return: String
        """
        return f'<User {self.username}>'


@login.user_loader
def load_user(id):
    """
    Loads the user by his id.
    @param id: String
    @return: User
    """
    return User.query.get(int(id))


class Post(db.Model):
    """ Model for representing the post table. """
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(1210))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        """
        String representation of Post class.
        @return: String
        """
        return f'<Post {self.body}>'
