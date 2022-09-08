""" Project wise config. """

import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """ Config class """
    ADMINS = ['towfiqahmed046@gmail.com']
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    ELASTICSEARCH_NAME = os.environ.get('ELASTICSEARCH_NAME')
    ELASTICSEARCH_PASS = os.environ.get('ELASTICSEARCH_PASS')
    LANGUAGES = ['bn', 'en']
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    POSTS_PER_PAGE = 25
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my-secret-key'
    MAIL_SENDGRID_API_KEY = os.environ.get('MAIL_SENDGRID_API_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(Config):
    """ Config class for testing """
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    TESTING = True
