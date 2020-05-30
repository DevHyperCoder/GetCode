from getcode import app,db
from getcode.models import User
from flask import Blueprint,request,redirect,url_for

authentication_api = Blueprint('authentication_api',__name__)

@authentication_api.route("/api/login",methods=['POST'])
def api_login():
    user = db.session.query(db.exists().where(
            User.email == request.form['email'])).scalar()
    if not user:
        return {"error":"User doesn't exist"}

    user = User.query.filter_by(email=request.form['email']).first()
    password = request.form['password']

    if not bcrypt.check_password_hash(user.password, password):
        return {"error":"Username or password doesn't match"}
    
    token = user.get_reset_token()

    return {"token":token}

