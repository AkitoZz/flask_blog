#coding:utf-8
from flask import render_template,redirect,request,url_for,flash
from . import auth
from .forms import LoginForm,RegistrationForm
from ..models import User
from flask_login import login_user,logout_user,login_required,current_user
from .. import db
from ..email import send_email

#login_user函数会回调User模型中装饰的load_user函数，并将其加到session中，这个考虑session多加一个token
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            #login_user(user, form.remember_me.data)
            #此处改为默认记住，因为todolist需要cookie里的值，暂时这么做
            login_user(user, True)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('账户或密码错误.')
    return render_template('auth/login.html', form=form)



@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('下次还要一起玩哦')
    return redirect(url_for('main.index'))

@auth.route('/register',methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user =User(email=form.email.data,
                    username = form.username.data,
                    password = form.password.data
                )
        db.session.add(user)
        db.session.commit()

        token = user.generate_confirmation_token()
        send_email(user.email,'请认证您的账户','auth/email/confirm',user=user,token=token)
        flash('一封身份认证邮件已发送到您的邮箱')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)    

@auth.route('confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('电波回路已同步')
    else:
        flash('认证链接已失效或超时')
    return redirect(url_for('main.index'))            

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '请认证您的账户',
               'auth/email/confirm', user=current_user, token=token)
    flash('一封身份认证邮件已发送到您的邮箱')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('密码已更新.')
            return redirect(url_for('main.index'))
        else:
            flash('密码错误.')
    return render_template("auth/change_password.html", form=form)
