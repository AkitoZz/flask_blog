from datetime import datetime
from flask import render_template,session,redirect,url_for,abort,flash,request,current_app

from . import main
from .froms import NameForm,EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from .. import db
from ..models import User,Role,Permission,Post,Comment

from ..decorators import admin_required,permission_required

from flask_login import login_required,current_user

'''
@main.route('/',methods=['GET','POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
    #    print('user:',user)
        if user is None:
            user = User(username = form.name.data)
            db.session.add(user)
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('.index'))
    return render_template('index.html',form=form,name=session.get('name'),known=session.get('known',False),current_time=datetime.utcnow())
'''

@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()    
    return render_template('user.html',user=user,posts=posts)    

@main.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('更人信息已更新')
        return redirect(url_for('.user',username=current_user.username))
    form.name.data = current_user.name
    form.location = current_user.location
    form.about_me = current_user.about_me
    return render_template('edit_profile.html',form=form)

@main.route('/edit-profile/<int:id>',methods=["GET","POST"])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('个人信息已更新.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

@main.route('/',methods=['GET','POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data,author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    #posts = Post.query.order_by(Post.timestamp.desc()).all()   
    page = request.args.get('page',1,type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_POSTS_PRE_PAGE'],error_out=False)
    posts = pagination.items
    return render_template('index.html',form=form,posts=posts,pagination=pagination)

@main.route('/post/<int:id>',methods=["GET","POST"])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                        post=post,
                        author=current_user._get_current_object()
        )
        db.session.add(comment)
        flash("评论提交成功！")
        return redirect(url_for('.post',id=post.id,page=-1))
    page = request.args.get('page',1,type=int)
    if page == -1:
        page = (post.comments.count() -1 ) // current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items        
    return  render_template('post.html',posts=[post],form=form,comments=comments,pagination=pagination)    



@main.route('/edit/<int:id>',methods=["GET","POST"])    
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('博客内容已更新')
        return redirect(url_for('.post',id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html',form=form)

@main.route('/moderate')    
@login_required
@permission_required(Permission.ADMINISTER)
def moderate():
    page = request.args.get('page',1,type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False)
    comments = pagination.items
    return render_template('moderate.html',comments=comments,pagination=pagination,page=page)

@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.ADMINISTER)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.ADMINISTER)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))    

@main.route('/todolist')                            
@login_required
def todolist():
    return redirect('http://127.0.0.1:8000/todolist')