from datetime import datetime

from flask import render_template, flash, redirect, url_for, request, g, jsonify, current_app
from flask_babel import _, get_locale
from flask_login import login_required, current_user
from googletrans import Translator

from app import db
from app.exceptions import LangDetectException
from app.helper import flash_message_and_redirect
from app.main import bp
from app.main.forms import EditProfileForm, EmptyForm, PostForm
from app.models import User, Post


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
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
        return flash_message_and_redirect(message=_('Your post is successful!'), endpoint=endpoint, category='success')
    return _render_template_with_pagination(endpoint=endpoint, template_name='index.html', title=_('Home'), form=form)


@bp.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return _render_template_with_pagination(endpoint='main.profile', template_name='profile.html', title=_('Profile'),
                                            form=form, user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        return flash_message_and_redirect(message=_('Your changes have been saved.'), endpoint='main.profile',
                                          category='success', username=current_user.username)
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    if _validate_form_on_submit(EmptyForm()):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return flash_message_and_redirect(
                message=_('User %(username)s not found.', username=username.capitalize()), endpoint='main.index',
                category='danger')
        if user == current_user:
            return flash_message_and_redirect(message=_('You cannot follow yourself!'), endpoint='main.profile',
                                              category='danger', username=username)
        current_user.follow(user)
        db.session.commit()
        return flash_message_and_redirect(
            message=_('You are now following %(username)s.', username=username.capitalize()), endpoint='main.profile',
            category='success', username=username)
    return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    if _validate_form_on_submit(EmptyForm()):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return flash_message_and_redirect(
                message=_('User %(username)s not found.', username=username.capitalize()), endpoint='main.index',
                category='danger')
        if user == current_user:
            return flash_message_and_redirect(message=_('You cannot unfollow yourself!'), endpoint='main.profile',
                                              category='danger', username=username)
        current_user.unfollow(user)
        db.session.commit()
        return flash_message_and_redirect(message=_('You unfollowed %(username)s.', username=username.capitalize()),
                                          endpoint='main.profile', category='success', username=username)
    return redirect(url_for('main.index'))


@bp.route('/explore')
@login_required
def explore():
    return _render_template_with_pagination(endpoint='main.explore', template_name='explore.html', title=_('Explore'))


@bp.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': Translator().translate(request.json['text'], request.json['dest_language'],
                                                   request.json['source_language']).text})


def _validate_form_on_submit(form):
    form = form
    return form.validate_on_submit()


def _render_template_with_pagination(*, endpoint, template_name, title, form=None, user=None):
    page = request.args.get('page', 1, type=int)
    if endpoint == 'main.index':
        posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    elif endpoint == 'main.profile':
        posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    else:
        posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for(endpoint, page=posts.next_num,
                       username=user.username if user else None) if posts.has_next else None
    prev_url = url_for(endpoint, page=posts.prev_num,
                       username=user.username if user else None) if posts.has_prev else None
    return render_template(template_name, title=title, posts=posts.items, next_url=next_url, prev_url=prev_url,
                           form=form, user=user, pagination=posts)
