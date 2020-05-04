from datetime import datetime

from getcode import db
from getcode import app
from flask_login import UserMixin

class User(db.Model, UserMixin):
    """Model for user accounts."""

    __tablename__ = 'users'

    id = db.Column(db.Integer,
                   primary_key=True)
    username = db.Column(db.String,
                         nullable=False,
                         unique=False)
    email = db.Column(db.String(40),
                      unique=True,
                      nullable=False)
    password = db.Column(db.String(200),
                         primary_key=False,
                         unique=False,
                         nullable=False)
    google_login=db.Column(db.Integer,unique=False,nullable=False)

    def get_reset_token(self,expires_sec=1800):
        # defualtis 30min
        s=Serializer(app.config['SECRET_KEY'],expires_sec)
        return s.dumps({"user_id": self.id}).decode('utf-8')

    @staticmethod
    def verifiy_reset_token(token):
        s=Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Snippet(db.Model):
    __tablename__ = 'code_snippets'
    __searchable__ =['name','description','code','email','tags']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.String, nullable=False, unique=False)
    email = db.Column(db.String(40),
                      unique=False,
                      nullable=False)
    code = db.Column(db.String, unique=False, nullable=False)
    created_date = db.Column(db.String, nullable=False, unique=False)
    likes = db.Column(db.Integer, primary_key=False,
                      nullable=False, unique=False)
    liked_users=db.Column(db.String,nullable = True,unique=False)
    comments = db.Column(db.String, nullable=True, unique=False)
    tags = db.Column(db.String,nullable=True,unique=False)
    visibility  =db.Column(db.Integer,nullable = True)

class Comments(db.Model):
    __tablename__='comments'
    id = db.Column(db.Integer, primary_key=True)
    email_of_commenter = db.Column(db.String(40),
                      unique=False,
                      nullable=False)
    created_date = db.Column(db.String, nullable=False, unique=False)
    comment = db.Column(db.String, nullable=False, unique=False)
    post_name = db.Column(db.String, nullable=False, unique=False)

db.init_app(app)