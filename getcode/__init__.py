from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from oauthlib.oauth2 import WebApplicationClient

import os

PUBLIC = 1
PRIVATE = 0
GOOGLE_LOGIN = 1
FACEBOOK_LOGIN = 2
GITHUB_LOGIN=3

MAINTANCE_MODE = os.environ.get('MAINTANCE_MODE')

# Configuration for Google Login
GOOGLE_CLIENT_ID = os.environ.get("CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Initialisation

app = Flask(__name__)

app.config.from_pyfile('config.py')

db = SQLAlchemy()

mail = Mail(app)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

bcrypt = Bcrypt(app)

jwt_manager = JWTManager(app)

login_manager = LoginManager()
login_manager.init_app(app)

from getcode.models import User

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


from getcode.snippet_view import snippet_view
from getcode.auth_view import auth_view
from getcode.authentication_views import authentication_views
from getcode.api_help import api_help
from getcode.snippet_api import snippet_api
from getcode.google_auth import google_auth

app.register_blueprint(snippet_view)
app.register_blueprint(auth_view)
app.register_blueprint(authentication_views)
app.register_blueprint(api_help)
app.register_blueprint(snippet_api)
app.register_blueprint(google_auth)

from getcode import routes
