from flask import url_for, redirect, render_template, request
from flask_babel import gettext
from flask_login import current_user, login_user, login_required, logout_user
from werkzeug.urls import url_parse

from app import db
from app.auth import bp
from app.auth.email import send_password_reset_email
from app.auth.forms import RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from app.helper import flash_message_and_redirect
from app.models import User


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return flash_message_and_redirect(
            message=gettext('Congratulations, you are now a registered user!'),
            endpoint='auth.login',
            category='success')
    return render_template('auth/register.html', title=gettext('Register'), form=form)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            return flash_message_and_redirect(
                message=gettext('Invalid username or password.'), endpoint='auth.login', category='warning')
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title=gettext('Sign In'), form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter(User.username == form.username.data, User.email == form.email.data).first()
        if user:
            send_password_reset_email(user)
        return flash_message_and_redirect(
            message=gettext("Thanks! If your Easyblogbd username and email address match, you'll get an email with a "
                            "link to reset your password shortly."), endpoint='auth.login', category='info')
    return render_template('auth/reset_password_request.html', title=gettext('Reset Password'), form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return flash_message_and_redirect(
            message=gettext('Invalid request.'), endpoint='auth.login', category='warning')
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        return flash_message_and_redirect(
            message=gettext('Your password has been reset.'), endpoint='auth.login', category='success')
    return render_template('auth/reset_password.html', form=form)
