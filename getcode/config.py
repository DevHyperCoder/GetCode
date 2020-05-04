import os

# Flask App Config
SECRET_KEY = os.environ.get('SECRET_KEY')


# Databse config
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask-Mail setup to use GMail
MAIL_SERVER=os.environ.get('MAIL_SERVER')
MAIL_PORT=os.environ.get('MAIL_PORT')
MAIL_USE_TLS=True
MAIL_USERNAME=os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD')