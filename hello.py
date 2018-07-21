from flask import request
from flask import Flask,render_template,session,redirect,url_for,flash
from flask import abort
from flask_script import Manager,Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import Form
from wtforms import StringField,SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
import os

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + os.path.join(basedir,'data.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True    
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)

def make_shell_context():
    return dict(app=app,db=db,User=User,Role=Role)
manager.add_command("Shell",Shell(make_context=make_shell_context))

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64),unique=True)

    users = db.relationship('User',backref='role')

    def __repr__(self):
        return '<Role %r>' % self.name    

class User(db.Model):
    __tablename__  = 'users'
    id = db.Column(db.Integer,primary_key=True)    
    username = db.Column(db.String(64),unique=True,index=True)
    role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))

    def __repr__(self):
        return '<User %r>'% self.username

class NameForm(Form):
    name = StringField('what is your name?',validators=[Required()])
    submit = SubmitField('Submit')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'),404

@app.route('/test')
def test():
    user_agent = request.headers.get('User-Agent')
    return '<p>your broswer is %s </p>' % user_agent
    #return request,type(request)

@app.route('/',methods=['GET','POST'])
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
        return redirect(url_for('index'))        
#        old_name = session.get('name')
#        if old_name is not None and old_name != form.name.data:
#            flash('Looks like you\'ve changed your name!')
#        session['name'] = form.name.data    
#        return redirect(url_for('index'))
    
    return render_template('index.html',form=form,name=session.get('name'),known = session.get('known',False),current_time=datetime.utcnow())

@app.route('/user/<name>')
def user(name):
#    user = load_user(name)
#    if not user:
 #       abort(404)
    return render_template('user.html',name=name)


if __name__ == '__main__':
#    app.run(debug=True)
    manager.run()    