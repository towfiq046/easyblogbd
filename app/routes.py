from datetime import datetime

from flask import render_template, flash, redirect, url_for, request, g, jsonify
from flask_babel import _, get_locale
from flask_login import login_required, current_user, login_user, logout_user
from googletrans import Translator
from werkzeug.urls import url_parse

from app import app, db
from app.email import send_password_reset_email
from app.exceptions import LangDetectException
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, ResetPasswordRequestForm, \
    ResetPasswordForm
from app.models import User, Post


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    endpoint = 'index'
    form = PostForm()
    if form.validate_on_submit():
        try:
            language = Translator().detect(form.post.data).lang
        except LangDetectException:
            language = ''
        post = Post(body=form.post.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
        return _flash_message_and_redirect(message=_('Your post is successful!'), endpoint=endpoint, category='success')
    return _render_template_with_pagination(endpoint=endpoint, template_name='index.html', title=_('Home'), form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return _flash_message_and_redirect(message=_('Congratulations, you are now a registered user!'),
                                           endpoint='login',
                                           category='success')
    return render_template('register.html', title=_('Register'), form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            return _flash_message_and_redirect(message=_('Invalid username or password.'), endpoint='login',
                                               category='warning')
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title=_('Sign In'), form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return _render_template_with_pagination(endpoint='profile', template_name='profile.html',
                                            title=_('Profile'), form=form, user=user)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        return _flash_message_and_redirect(message=_('Your changes have been saved.'), endpoint='profile',
                                           category='success', username=current_user.username)
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'), form=form)


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    if _validate_form_on_submit(EmptyForm()):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return _flash_message_and_redirect(
                message=_('User %(username)s not found.', username=username.capitalize()), endpoint='index',
                category='danger')
        if user == current_user:
            return _flash_message_and_redirect(message=_('You cannot follow yourself!'), endpoint='profile',
                                               category='danger', username=username)
        current_user.follow(user)
        db.session.commit()
        return _flash_message_and_redirect(
            message=_('You are now following %(username)s.', username=username.capitalize()), endpoint='profile',
            category='success', username=username)
    return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    if _validate_form_on_submit(EmptyForm()):
        user = User.query.filter_by(username=username).first()
        if user is None:
            return _flash_message_and_redirect(
                message=_('User %(username)s not found.', username=username.capitalize()), endpoint='index',
                category='danger')
        if user == current_user:
            return _flash_message_and_redirect(message=_('You cannot unfollow yourself!'), endpoint='profile',
                                               category='danger', username=username)
        current_user.unfollow(user)
        db.session.commit()
        return _flash_message_and_redirect(message=_('You unfollowed %(username)s.', username=username.capitalize()),
                                           endpoint='profile', category='success', username=username)
    return redirect(url_for('index'))


@app.route('/explore')
@login_required
def explore():
    return _render_template_with_pagination(endpoint='explore', template_name='explore.html', title=_('Explore'))


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username == form.username.data, User.email == form.email.data).first()
        if user:
            send_password_reset_email(user)
        return _flash_message_and_redirect(message=_("Thanks! If your Microblog username and email address match, "
                                                     "you'll get an email with a link to reset your password shortly."),
                                           endpoint='login', category='info')
    return render_template('reset_password_request.html', title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        return _flash_message_and_redirect(message=_('Your password has been reset.'), endpoint='login',
                                           category='success')
    return render_template('reset_password.html', form=form)


@app.route('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify({'text': Translator().translate(request.json['text'], request.json['dest_language'],
                                                   request.json['source_language']).text})


def _validate_form_on_submit(form):
    form = form
    return form.validate_on_submit()


def _flash_message_and_redirect(*, message: str, endpoint: str, category: str = '', username: str = None):
    flash(message, category)
    if endpoint == 'profile':
        return redirect(url_for(endpoint, username=username))
    return redirect(url_for(endpoint))


def _render_template_with_pagination(*, endpoint, template_name, title, form=None, user=None):
    page = request.args.get('page', 1, type=int)
    if endpoint == 'index':
        posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
    elif endpoint == 'profile':
        posts = user.posts.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    else:
        posts = Post.query.order_by(Post.timestamp.desc()).paginate(page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for(endpoint, page=posts.next_num,
                       username=user.username if user else None) if posts.has_next else None
    prev_url = url_for(endpoint, page=posts.prev_num,
                       username=user.username if user else None) if posts.has_prev else None
    return render_template(template_name, title=title, posts=posts.items, next_url=next_url, prev_url=prev_url,
                           form=form, user=user, pagination=posts)
