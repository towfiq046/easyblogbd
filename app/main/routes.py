from datetime import datetime

from elastic_transport import ConnectionError
from flask import (current_app, flash, g, jsonify, redirect, render_template, request, url_for)
from flask_babel import get_locale, gettext
from flask_login import current_user, login_required
from googletrans import Translator
from redis.exceptions import ConnectionError

from app import db
from app.exceptions import LangDetectException
from app.helper import flash_message_and_redirect
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, MessageForm, PostForm, SearchForm
from app.models import Message, Notification, Post, User


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    endpoint = 'main.index'
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = Translator().detect(form.post.data).lang
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        return flash_message_and_redirect(
            message=gettext('Your post is successful!'), endpoint=endpoint, category='success')
    pagination = current_user.followed_posts().paginate(
        request.args.get('page', 1, type=int), current_app.config['POSTS_PER_PAGE'], False)
    return _render_template_with_pagination(
        endpoint=endpoint, pagination=pagination, template_name='index.html', title=gettext('Home'), form=form)


@bp.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        request.args.get('page', 1, type=int), current_app.config['POSTS_PER_PAGE'], False)
    return _render_template_with_pagination(
        endpoint='main.profile', pagination=pagination, template_name='profile.html', title=gettext('Profile'),
        form=EmptyForm(), user=user)


@bp.route('/profile/<username>/popup')
@login_required
def profile_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('profile_popup.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        return flash_message_and_redirect(
            message=gettext('Your changes have been saved.'), endpoint='main.profile', category='success',
            username=current_user.username)
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=gettext('Edit Profile'), form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    if EmptyForm().validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            return flash_message_and_redirect(
                message=gettext('User %(username)s not found.', username=username.capitalize()), endpoint='main.index',
                category='danger')
        if user == current_user:
            return flash_message_and_redirect(
                message=gettext('You cannot follow yourself!'), endpoint='main.profile', category='danger',
                username=username)
        current_user.follow(user)
        db.session.commit()
        return flash_message_and_redirect(
            message=gettext('You are now following %(username)s.',
                            username=username.capitalize()),
            endpoint='main.profile', category='success', username=username)
    return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    if EmptyForm().validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            return flash_message_and_redirect(
                message=gettext('User %(username)s not found.', username=username.capitalize()), endpoint='main.index',
                category='danger')
        if user == current_user:
            return flash_message_and_redirect(
                message=gettext('You cannot unfollow yourself!'), endpoint='main.profile', category='danger',
                username=username)
        current_user.unfollow(user)
        db.session.commit()
        return flash_message_and_redirect(
            message=gettext('You unfollowed %(username)s.',
                            username=username.capitalize()),
            endpoint='main.profile', category='success', username=username)
    return redirect(url_for('main.index'))


@bp.route('/explore')
@login_required
def explore():
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        request.args.get('page', 1, type=int), current_app.config['POSTS_PER_PAGE'], False)
    return _render_template_with_pagination(
        endpoint='main.explore', pagination=pagination, template_name='explore.html', title=gettext('Explore'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({
        'text': Translator().translate(
            request.json['text'], request.json['dest_language'], request.json['source_language']).text})


@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    text_to_search = g.search_form.q.data
    page = request.args.get('page', 1, type=int)
    # Catching the ConnectionError here not in search.py to show user a message.
    try:
        posts, total_number_of_posts = Post.search(text_to_search, page, current_app.config['POSTS_PER_PAGE'])
    except ConnectionError:
        return render_template('errors/503.html', title='503')
    next_url = url_for(
        'main.search', q=text_to_search, page=page + 1) if total_number_of_posts > page * current_app.config[
        'POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=text_to_search, page=page - 1) if page > 1 else None
    return render_template('search.html', title='Search', posts=posts, prev_url=prev_url, next_url=next_url,
                           total_number_of_posts=total_number_of_posts, text_to_search=text_to_search)


@bp.route('/send_message/<receiver>', methods=['GET', 'POST'])
@login_required
def send_message(receiver):
    user = User.query.filter_by(username=receiver).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        message = Message(author=current_user, receiver=user, body=form.message.data)
        user.add_notification('unread_message_count', user.count_new_messages())
        db.session.add(message)
        db.session.commit()
        return flash_message_and_redirect(
            message=gettext('Your message has been sent.'), category='success', endpoint='main.profile',
            username=receiver)
    return render_template('send_message.html', title=gettext('Send Message'),
                           form=form, receiver=receiver)


@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    pagination = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
        request.args.get('page', 1, type=int), current_app.config['POSTS_PER_PAGE'], False)
    return _render_template_with_pagination(
        endpoint='main.messages', pagination=pagination, template_name='messages.html', title=gettext('Messages'))


@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    notifications = current_user.notifications.filter(
        Notification.timestamp > since).order_by(Notification.timestamp)
    return jsonify([{
        'name': notification.name,
        'data': notification.get_data(),
        'timestamp': notification.timestamp
    } for notification in notifications])


@bp.route('/export_posts')
@login_required
def export_posts():
    try:
        if current_user.get_task_in_progress('export_posts'):
            flash(gettext('An export task is currently in progress'))
        current_user.launch_task('export_posts', gettext('Exporting posts...'))
        db.session.commit()
        return redirect(url_for('main.profile', username=current_user.username))
    except ConnectionError:
        return render_template('errors/503.html', title='503')


def _render_template_with_pagination(*, endpoint, pagination, template_name, title, form=None, user=None):
    next_url = url_for(
        endpoint, page=pagination.next_num, username=user.username if user else None) if pagination.has_next else None
    prev_url = url_for(
        endpoint, page=pagination.prev_num, username=user.username if user else None) if pagination.has_prev else None
    return render_template(
        template_name, title=title, posts=pagination.items, next_url=next_url,
        prev_url=prev_url, form=form, user=user, pagination=pagination)
