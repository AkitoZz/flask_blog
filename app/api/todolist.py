from flask import jsonify,request,g,current_app,url_for,redirect,url_for
from .. import db
from . import api
from .errors import forbidden
from .decorators import permission_required
from ..models import Todolist
from functools import wraps
import json     


#未加权限处理，有before_request的用户认证即可
#该装饰器未使用，用flask_cors扩展解决跨域问题
def cors(func):  
    @wraps(func)
    def wrapper_func(*args, **kwargs):
        r = make_response(func(*args, **kwargs))
        r.headers['Access-Control-Allow-Origin'] = '*'
        r.headers['Access-Control-Allow-Methods'] = 'HEAD, OPTIONS, GET, POST, DELETE, PUT'
        allow_headers = "Referer, Accept, Origin, User-Agent, X-Requested-With, Content-Type"
        r.headers['Access-Control-Allow-Headers'] = allow_headers
        # if you need the cookie access, uncomment this line
        r.headers['Access-Control-Allow-Credentials'] = 'true'
        return r

    return wrapper_func



@api.route('/todolist',methods=['POST'])
def get_todolist():
    # if request.method == 'OPTIONS':
    #     print('[debug][todolist]',request.method)
    #     return redirect(url_for('api.get_todolist')),203
    print('[debug][req_params]',request.values,request.form,request.args,request.data.decode('utf-8'))
    #此处用data获取，疑问点
    res = json.loads(request.data.decode('utf-8'))
    if not res.get('mod'):
        return jsonify({'error':{'error_id':-2,'reason':'缺少参数'}})
    mod = res.get('mod')
    user_id = g.current_user.id
    todolist = Todolist.query.filter_by(user_id=user_id).all()
    if mod == 'list':
        return jsonify({'error':{'error_id':0,'reason':'success'},'data':[x.to_json() for x in todolist ]})
    if mod == 'create':
        todolist_new = Todolist(user_id=user_id,title=res.get('title'),desp=res.get('desp'),s_time=res.get('s_time'),e_time=res.get('e_time'))
        #flask_sqlalchemy暂时不知道怎么抛出异常，只好对unique列进行判断
        print('[debug][jug]',Todolist.query.filter_by(title=res.get('title')).first())
        if Todolist.query.filter_by(title=res.get('title')).first() == None:
            db.session.add(todolist_new)
            db.session.commit()
            todolist = Todolist.query.filter_by(user_id=user_id).all()
            return jsonify({'error':{'error_id':0,'reason':'success'},'data':[x.to_json() for x in todolist]})
        else:
            return jsonify({'error':{'error_id':-3,'reason':'计划项已存在,新建失败'}})
    if mod == 'edit':
        id = res.get('id')
        todolist_edit = Todolist.query.filter_by(id=id).first()
        todolist_edit.title = res.get('title')
        todolist_edit.desp = res.get('desp')
        todolist_edit.s_time = res.get('s_time')
        todolist_edit.e_time = res.get('e_time')
        db.session.add(todolist_edit)
        db.session.commit()
        todolist = Todolist.query.filter_by(user_id=user_id).all()
        return jsonify({'error':{'error_id':0,'reason':'success'},'data':[x.to_json() for x in todolist]})
    if mod == 'delete':
        id = res.get('id')
        todolist_del = Todolist.query.filter_by(id=id).first()
        db.session.delete(todolist_del)
        db.session.commit()
        todolist = Todolist.query.filter_by(user_id=user_id).all()
        return jsonify({'error':{'error_id':0,'reason':'success'},'data':[x.to_json() for x in todolist]})
    if mod == 'done':
        id = res.get('id')
        todolist_done = Todolist.query.filter_by(id=id).first()
        todolist_done.status = True
        db.session.add(todolist_done)
        db.session.commit()
        todolist = Todolist.query.filter_by(user_id=user_id).all()
        return jsonify({'error':{'error_id':0,'reason':'success'},'data':[x.to_json() for x in todolist]})

