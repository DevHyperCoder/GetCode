import os,secrets
import datetime
# Flask App Config
SECRET_KEY = os.environ.get('SECRET_KEY')

if SECRET_KEY is "" or SECRET_KEY is None:
    # Set up a random
    SECRET_KEY=os.urandom(16)


# Databse config
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Mail setup to use GMail
MAIL_SERVER=os.environ.get('MAIL_SERVER')
MAIL_PORT=os.environ.get('MAIL_PORT')
MAIL_USE_SSL=True
MAIL_USERNAME=os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')

#JWT Extension
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if JWT_SECRET_KEY is None or "":
    JWT_SECRET_KEY = os.urandom(16)

EXPIRY_DELTA = datetime.timedelta(days=365)