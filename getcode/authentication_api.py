from getcode.utils import does_user_exist
from flask import Blueprint, request
from getcode import bcrypt, db
from flask_jwt_extended import create_access_token
from getcode.models import User
from getcode.config import EXPIRY_DELTA

authentication_api = Blueprint('authentication_api', __name__)


@authentication_api.route("/api/login", methods=['POST'])
def login_api():
    json = request.get_json()
    email = json.get('email')
    user_exists = db.session.query(db.exists().where(
        User.email == email)).scalar()
    if not user_exists:
        return {"error": "User doesn't exist"}

    user = User.query.filter_by(email=email).first()
    password = json.get('password')

    if bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(
            identity=user.username,
            expires_delta=EXPIRY_DELTA)

        return {"success": access_token}

    return {"error": "invalid credentials"}


@authentication_api.route("/api/signup",methods=['POST'])
def signup_api():
    json = request.get_json()
    username = json.get("username")
    username_exists = does_user_exist(username=username)
    if username_exists:
        return {"error": "username exists"}
    
    email = json.get("email")
    email_exists = does_user_exist(email=email)
    if email_exists:
        return {"error":"email exists"}
    
    password = json.get("password")
    hashed_pass = bcrypt.generate_password_hash(password).decode('utf-8')

# TODO add the code to randomly generate the user_id

    user = User(username=username,
                    email=email, 
                    password=hashed_pass)

    db.session.add(user)
    db.session.commit()
    return {"success": "added bro"}
