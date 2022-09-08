# pylint: disable=no-member
import json
from datetime import datetime
from hashlib import md5
from time import time

import jwt
from flask import current_app
from flask_login import UserMixin
from jwt import DecodeError, ExpiredSignatureError
from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError
from rq.job import Job
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from app.constants import (
    ABOUT_ME_LENGTH, EMAIL_LENGTH, PASSWORD_LENGTH, USERNAME_LENGTH, POST_LENGTH, MESSAGE_LENGTH, NAME_LENGTH)
from app.search import add_to_index, query_index, remove_from_index

followers = db.Table('followers', db.Column('follower_id', db.Integer, db.ForeignKey(
    'user.id')), db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))


class User(UserMixin, db.Model):
    """ Model class for representing the user table. """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(USERNAME_LENGTH), index=True, unique=True)
    email = db.Column(db.String(EMAIL_LENGTH), index=True, unique=True)
    password_hash = db.Column(db.String(PASSWORD_LENGTH))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(ABOUT_ME_LENGTH))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_read_time = db.Column(db.DateTime)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    followed = db.relationship(
        'User',
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic')
    messages_sent = db.relationship(
        'Message',
        foreign_keys='Message.sender_id',
        backref='author', lazy='dynamic')
    # Using 'author' instead of 'sender' For the benefit of reusing like this (post.author) in _post.html.
    messages_received = db.relationship(
        'Message',
        foreign_keys='Message.receiver_id',
        backref='receiver', lazy='dynamic')

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
        own_post = Post.query.filter_by(user_id=self.id)
        return followed.union(own_post).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        """
        Get the token to reset password.
        @param expires_in: Integer
        @return: String
        """
        return jwt.encode(
            {
                'reset_password': self.id,
                'exp': time() + expires_in
            },
            current_app.config['SECRET_KEY'],
            algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        """
        Verifies token which is used to reset password, return the id of the user.
        @param token: String
        @return: Integer
        """
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except (DecodeError, ExpiredSignatureError):
            return
        return User.query.get(id)

    def count_new_messages(self):
        """
        Counts the number of new messages.
        @return: Integer
        """
        return Message.query \
            .filter_by(receiver=self) \
            .filter(Message.timestamp > (self.last_message_read_time or datetime(1900, 1, 1))).count()

    def add_notification(self, name, data):
        """
        Removes any previous notification and adds notification to the session.
        @param name: String
        @param data: Integer
        @return: Notification object
        """
        self.notifications.filter_by(name=name).delete()
        notification = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(notification)
        return notification

    def launch_task(self, name, description, *args, **kwargs):
        """
        Creates a job and returns the task.
        @param name: String
        @param description: String
        @return: Task object
        """
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id, *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        """
        Returns all the incomplete tasks.
        @return: Task object
        """
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        """
        Returns a single task.
        @param name: String
        @return: Task object
        """
        return Task.query.filter_by(name=name, user=self, complete=False).first()

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


class SearchableMixin:
    """ SearchableMixin class. """

    @classmethod
    def search(cls, text_to_search, page, per_page):
        """
        Returns user id in a serial and number of posts, in a tuple.
        @param text_to_search: String
        @param page: Integer
        @param per_page: Integer
        @return: Tuple
        """
        list_of_ids, total_number_of_posts = query_index(cls.__tablename__, text_to_search, page, per_page)
        if total_number_of_posts == 0:
            return cls.query.filter_by(id=0), 0
        id_serial = [(list_of_ids[i], i) for i in range(len(list_of_ids))]
        return cls.query.filter(cls.id.in_(list_of_ids)).order_by(
            db.case(id_serial, value=cls.id)), total_number_of_posts

    @classmethod
    def before_commit(cls, session):
        """
        Adds a dictionary of objects that are added, modified and deleted, to session._changes.
        @param session: Sqlalchemy session object
        @return: Dictionary
        """
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        """
        Adds, updates and deletes to elasticsearch index.
        @param session: Sqlalchemy session object
        @return: None
        """
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        """
        Adds data to elasticsearch index.
        @return: None
        """
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


class Post(SearchableMixin, db.Model):
    """ Model class for representing the post table. """
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(POST_LENGTH))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):
        """
        String representation of Post class.
        @return: String
        """
        return f'<Post {self.body}>'


class Message(db.Model):
    """ Model class for representing the message table. """
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(MESSAGE_LENGTH))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        """
        String representation of Message class.
        @return: String
        """
        return f'<Message {self.body}>'


class Notification(db.Model):
    """ Model class for representing the notification table. """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(NAME_LENGTH), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def get_data(self):
        """
        Deserializes the payload_json to python object.
        @return: Python object
        """
        return json.loads(str(self.payload_json))

    def __repr__(self):
        """
        String representation of Notification class.
        @return: String
        """
        return f'<Notification {self.body}>'


class Task(db.Model):
    """ Model class for representing the task table. """
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(NAME_LENGTH), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        """
        Fetches rq job instance according to the task id.
        @return: Job instance or None
        """
        try:
            rq_job = Job.fetch(self.id, connection=current_app.redis)
        except (RedisError, NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        """
        Returns the job progress percentage.
        @return: Integer
        """
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)
