from datetime import datetime, timedelta

import pytest

from app import db, create_app
from app.models import User, Post
from config import TestConfig


def create_user(username='test-user', email='test@mail.com'):
    return User(username=username, email=email)


def users_added_to_db():
    joshim = create_user('joshim', 'joshim@mail.com')
    shabana = create_user('shabana', 'shabana@mail.com')
    db.session.add(joshim)
    db.session.add(shabana)
    db.session.commit()
    return joshim, shabana


@pytest.fixture
def app():
    app = create_app(TestConfig)
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    yield app

    db.session.remove()
    db.drop_all()
    app_context.pop()


def test_check_password_hash_with_wrong_password():
    user = create_user()
    password = 'pass'
    wrong_password = 'wrong pass'
    user.set_password(password)
    assert user.check_password(wrong_password) is False


def test_check_password_hash_with_correct_password():
    user = create_user()
    password = 'pass'
    user.set_password(password)
    assert user.check_password(password) is True


def test_avatar():
    user = create_user()
    assert user.avatar(128) == 'https://www.gravatar.com/avatar/97dfebf4098c0f5c16bca61e2b76c373?d=retro&s=128'


def test_follower_count_without_follower(app):
    joshim, shabana = users_added_to_db()
    assert shabana.followers.count() == 0


def test_follower_count_with_follower(app):
    joshim, shabana = users_added_to_db()
    joshim.follow(shabana)
    assert shabana.followers.count() == 1


def test_followed_count_without_following_anyone(app):
    joshim, shabana = users_added_to_db()
    assert joshim.followed.count() == 0


def test_followed_count_after_following_someone(app):
    joshim, shabana = users_added_to_db()
    joshim.follow(shabana)
    assert joshim.followed.count() == 1


def test_user_is_not_following_another_user(app):
    joshim, shabana = users_added_to_db()
    assert joshim.is_following(shabana) is False


def test_user_is_following_another_user(app):
    joshim, shabana = users_added_to_db()
    joshim.follow(shabana)
    assert joshim.is_following(shabana) is True


def test_user_unfollows_another_user(app):
    joshim, shabana = users_added_to_db()
    joshim.follow(shabana)
    joshim.unfollow(shabana)
    assert joshim.is_following(shabana) is False


def test_follower_count_after_unfollow(app):
    joshim, shabana = users_added_to_db()
    joshim.follow(shabana)
    joshim.unfollow(shabana)
    assert shabana.followers.count() == 0


def test_followed_count_after_unfollow(app):
    joshim, shabana = users_added_to_db()
    joshim.follow(shabana)
    joshim.unfollow(shabana)
    assert joshim.followed.count() == 0


def test_follow_post(app):
    joshim = create_user('joshim', 'joshim@mail.com')
    shabana = create_user('shabana', 'shabana@mail.com')
    rubel = create_user('rubel', 'rubel@mail.com')
    alomgir = create_user('alomgir', 'alomgir@mail.com')
    db.session.add_all([joshim, shabana, rubel, alomgir])

    now = datetime.utcnow()
    joshim_post = Post(body='post from joshim', author=joshim, timestamp=now + timedelta(seconds=1))
    shabana_post = Post(body='post from shabana', author=shabana, timestamp=now + timedelta(seconds=2))
    rubel_post = Post(body='post from rubel', author=rubel, timestamp=now + timedelta(seconds=3))
    alomgir_post = Post(body='post from alomgir', author=alomgir, timestamp=now + timedelta(seconds=4))
    db.session.add_all([joshim_post, shabana_post, rubel_post, alomgir_post])
    db.session.commit()

    joshim.follow(shabana)
    joshim.follow(alomgir)
    shabana.follow(rubel)
    rubel.follow(alomgir)
    db.session.commit()

    joshim_followed_posts = joshim.followed_posts().all()
    shabana_followed_posts = shabana.followed_posts().all()
    rubel_followed_posts = rubel.followed_posts().all()
    alomgir_followed_posts = alomgir.followed_posts().all()

    assert joshim_followed_posts == [alomgir_post, shabana_post, joshim_post]
    assert shabana_followed_posts == [rubel_post, shabana_post]
    assert rubel_followed_posts == [alomgir_post, rubel_post]
    assert alomgir_followed_posts == [alomgir_post]


def test_reset_password_token(app):
    user = create_user()
    assert user.get_reset_password_token()


def test_verify_reset_password_token(app):
    joshim, _ = users_added_to_db()
    token = joshim.get_reset_password_token()
    assert User.verify_reset_password_token(token) == joshim


def test_verify_reset_password_token_returns_none(app):
    joshim, _ = users_added_to_db()
    assert joshim.verify_reset_password_token('wrong-token') is None
