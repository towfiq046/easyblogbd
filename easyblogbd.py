from app import cli, create_app, db
from app.models import followers, Message, Notification, Post, Task, User
from config import Config

app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {'app': app, 'db': db, 'User': User, 'Post': Post, 'followers': followers, 'Config': Config,
            'Message': Message, 'Notification': Notification, 'Task': Task}
