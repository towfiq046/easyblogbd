import unittest
from datetime import datetime, timedelta

from app import app, db
from app.models import User, Post


def create_user(username='test-user', email='test@mail.com'):
    return User(username=username, email=email)


class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        user = create_user()
        password = 'pass'
        wrong_password = 'wrong-pass'
        user.set_password(password)
        self.assertFalse(user.check_password(wrong_password))
        self.assertTrue(user.check_password(password))

    def test_avatar(self):
        user = create_user()
        self.assertEqual(user.avatar(128), 'https://www.gravatar.com/avatar/97dfebf4098c0f5c16bca61e2b76c373'
                                           '?d=retro&s=128')

    def test_follow_and_unfollow(self):
        joshim = create_user('joshim', 'joshim@mail.com')
        shabana = create_user('shabana', 'shabana@mail.com')
        db.session.add(joshim)
        db.session.add(shabana)
        db.session.commit()

        self.assertEqual(joshim.followed.count(), 0)
        self.assertEqual(joshim.followers.count(), 0)

        joshim.follow(shabana)
        db.session.commit()

        self.assertTrue(joshim.is_following(shabana))
        self.assertEqual(joshim.followed.count(), 1)
        self.assertEqual(joshim.followed.first().username, 'shabana')
        self.assertEqual(shabana.followers.count(), 1)
        self.assertEqual(shabana.followers.first().username, 'joshim')

        joshim.unfollow(shabana)

        self.assertFalse(joshim.is_following(shabana))
        self.assertEqual(joshim.followed.count(), 0)
        self.assertEqual(shabana.followers.count(), 0)

    def test_follow_post(self):
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

        self.assertEqual(joshim_followed_posts, [alomgir_post, shabana_post, joshim_post])
        self.assertEqual(shabana_followed_posts, [rubel_post, shabana_post])
        self.assertEqual(rubel_followed_posts, [alomgir_post, rubel_post])
        self.assertEqual(alomgir_followed_posts, [alomgir_post])


if __name__ == '__main__':
    unittest.main(verbosity=2)
