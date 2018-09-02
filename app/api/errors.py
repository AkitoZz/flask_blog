from flask import jsonify
from app.exceptions import ValidationError
from . import api

#这里状态值全部改为200(非401等)，因为200才能把返回值交给前端，让前端去做处理

def bad_request(message):
    response = jsonify({'error': {'error_id':-1,'reason':'bad request %s'%(message)}})
    response.status_code = 200
    return response


def unauthorized(message):
    response = jsonify({'error': {'error_id':-1,'reason':'unauthorized %s'%(message)}})
    response.status_code = 200
    return response


def forbidden(message):
    response = jsonify({'error': {'error_id':-99,'reason':'forbidden %s' %(message)}})
    response.status_code = 200
    return response


@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])