from getcode.models import User,Snippet
from getcode import db
from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required
from getcode.utils import does_user_exist
user_api = Blueprint('user_api',__name__)

@user_api.route("/api/user")
@jwt_required
def get_current_user():
    username = get_jwt_identity()

    user = User.query.filter_by(username=username).first()

    if not user:
        return {"error":"no user found"}
    
    return {"user":user.serialize}


@user_api.route("/api/user/snippets")
@jwt_required
def get_snippets():
    username=get_jwt_identity()

    if not does_user_exist(username=username):
        return {"error":"no user found"}
    
    all_snippets_by_user = Snippet.query.filter_by(created_by_username = username)

    return {"snippets": [i.serialize for i in all_snippets_by_user]}

@user_api.route("/api/user/id/<string:id>")
@jwt_required
def get_user(id):
    user = User.query.filter_by(id=id).first()

    if not user:
        return{"user":"no user found"}

    return user.serialize
    