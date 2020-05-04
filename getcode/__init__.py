from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail,Message

from oauthlib.oauth2 import WebApplicationClient

from getcode.snippet_view import snippet_view


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

login_manager = LoginManager()
login_manager.init_app(app)

app.register_blueprint(snippet_view)



from getcode import routes
