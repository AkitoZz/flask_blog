from flask import jsonify,request,g,current_app,url_for
from .. import db
from . import api
from .errors import forbidden
from .decorators import permission_required
from ..models import Todolist

#未加权限处理，有before_request的用户认证即可

@api.route('/todolist',methods=['POST'])
def get_todolist():
    print('123',request.form)
    if not request.form.get('mod'):
        return jsonify({'error_id':-1,'error':'lost params'})
    mod = request.form.get('mod')
    user_id = g.current_user.id
    todolist = Todolist.query.filter_by(user_id=user_id).all()
    print('todo##########:',g.current_user,todolist,request.args)
    if mod == 'list':
        return jsonify([x.to_json() for x in todolist ])
    if mod == 'create':
        return 'create'
    if mod == 'edit':
        return 'edit'
