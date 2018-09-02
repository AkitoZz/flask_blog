from flask import g, jsonify,request
from flask_httpauth import HTTPBasicAuth
from flask_httpauth import HTTPTokenAuth
from ..models import User
from . import api
from .errors import unauthorized, forbidden

# auth = HTTPBasicAuth()


# @auth.verify_password
# def verify_password(email_or_token, password):
#     print('[debug][verify]',email_or_token,password,type(password),request)
#     if email_or_token == '':
#         return False
#     if password == '':
#         g.current_user = User.verify_auth_token(email_or_token)
#         g.token_used = True
#         print('[debug][verify1]')
#         return g.current_user is not None
#     user = User.query.filter_by(email=email_or_token).first()
#     if not user:
#         return False
#     g.current_user = user
#     g.token_used = False
#     return user.verify_password(password)

# auth = HTTPTokenAuth(scheme='Bearer')

# @auth.verify_token
# def verify_token(token):
#     print('[debug][verify_token]',token)
#     g.current_user = None
#     try:
#         user = User.verify_auth_token(token)
#         g.current_user = user
#         return True
#     except:
#         return False
#     return False


# @auth.error_handler
# def auth_error():
#     return unauthorized('Invalid credentials')


@api.before_request
#@auth.login_required
def before_request():
    #print('[debug][api before]',g.current_user)
    user = None
    token = request.headers.get('token')
    user = User.verify_auth_token(token)
    print('[debug][api before]',token,user)
    if user == None:
        return forbidden('token已过期请重新登陆')
    else:
        g.current_user = user

    # if g.current_user == None:
    #     return forbidden('未认证用户')
    # if not g.current_user.is_anonymous and \
    #         not g.current_user.confirmed:
    #     return forbidden('Unconfirmed account')


@api.route('/tokens', methods=['POST','GET'])
#@api.route('/tokens')
def get_token():
    #if g.current_user.is_anonymous or g.token_used:
    if g.current_user == None:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
