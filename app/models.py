from . import db
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin,AnonymousUserMixin
from . import login_manager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app,request,url_for,session,g
from datetime import datetime
import hashlib
from markdown import markdown
import bleach
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

#暂时发现只有跳转的时候会触发这个回调
# @login_manager.request_loader
# def load_user_from_request(request):
#     print("[debug][request_loader][header]",request.headers.get('token'))
#     print('[debug][request_loader][g]',g,g.current_user)
#     return None


#修改回调函数，返回值同样是user类，只是默认使用user_id查询，现改为使用token获取,并将用户存到g中
# 对api的请求而言，用户存储放在api蓝本认证处理中，也会设置g，以便后续获取数据
@login_manager.user_loader
def load_user(user_id):
    print("[debug][token]%s" %(user_id))
    user = User.verify_auth_token(user_id)
    g.current_user = user
    print('[debug][g]',g.current_user   )
    print("[debug][userid]%s"%(user))
    print("[debug][session%s]"%(session))
    return user

# @login_manager.user_loader
# def load_user(user_id):
#     print("[debug][session]%s" %(session))
#     return User.query.get(int(user_id))

class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')
    default = db.Column(db.Boolean,default=False,index=True)
    permissions = db.Column(db.Integer)

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            'User':(Permission.FOLLOW |
                    Permission.COMMENT,True
            ),
            'Moderator': (
                    Permission.FOLLOW |
                    Permission.COMMENT |
                    Permission.WRITE_ARTICLES |
                    Permission.MODERATE_COMMENTS,False
            ),
            'Administrator': (0xff,False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()        


class User(UserMixin,db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64),unique=True,index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean,default=False)

    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(),default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(),default=datetime.utcnow)

    posts = db.relationship('Post',backref='author',lazy='dynamic')
    comments = db.relationship('Comment',backref='author',lazy='dynamic')
    todolist = db.relationship('Todolist',backref='author',lazy='dynamic')

    avatar_hash = db.Column(db.String(32))

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()        
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()                


#loginmanager中的login_user()会调用Usermixin类中的get_id方法返回User类中的id，此处定义后会调用这个方法，返回token
    def get_id(self):
        return self.generate_auth_token(expiration=43200)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)           

    def can(self,permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)    

    def generate_confirmation_token(self,expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self,token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True        
    
    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()    

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)
    
    @property
    def password(self):
        raise AttributeError('passwd is not a readable attribute')

    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)        

    def __repr__(self):
        return '<User %r>' % self.username        

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                    username=forgery_py.internet.user_name(True),
                    password=forgery_py.lorem_ipsum.word(),
                    confirmed=True,
                    name=forgery_py.name.full_name(),
                    location=forgery_py.lorem_ipsum.sentence(),
                    member_since=forgery_py.date.date(True)
            )
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

    def generate_auth_token(self,expiration):
        s = Serializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])    

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    comments = db.relationship('Comment',backref='post',lazy='dynamic')

    body_html = db.Column(db.Text)

    @staticmethod
    def generate_fake(count=100):
        from random import seed,randint
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0,user_count -1)).first()
            p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),
                    timestamp=forgery_py.date.date(True),
                    author=u
            )
            db.session.add(p)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count()
        }
        return json_post

db.event.listen(Post.body, 'set', Post.on_changed_body)

class AnonymouseUser(AnonymousUserMixin):
    def can(self,permissions):
        return False

    def is_administrator(self):
        return False

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disable = db.Column(db.Boolean,default=True)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code',
                        'em', 'i',  'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

db.event.listen(Comment.body, 'set', Comment.on_changed_body)

class Todolist(db.Model):
    __tablename__ = 'todolist'
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    title = db.Column(db.String(64),unique=True)
    desp = db.Column(db.Text)
    s_time = db.Column(db.String(64))
    e_time = db.Column(db.String(64))
    status = db.Column(db.Boolean,default=False)

    def to_json(self):
        json_todolist = {
            'id':self.id,
            'user_id':self.user_id,
            'title':self.title,
            'desp':self.desp,
            's_time':self.s_time,
            'e_time':self.e_time,
            'status':self.status,
        }
        return json_todolist

login_manager.anonymous_user = AnonymouseUser        

