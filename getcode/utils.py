from getcode import db
from getcode.models import User, Snippet
from flask_login import current_user

def does_user_exist(email=None, username=None):
    if email is not None:
        # Email is given
        return db.session.query(db.exists().where(
            User.email == email)).scalar()

    if username is not None:
        # Username is given
        return db.session.query(db.exists().where(
            User.username == username)).scalar()


def does_snippet_exist(title=None,snippet_id=None):
    if title is not None:
        return db.session.query(db.exists().where(
            Snippet.name == title)).scalar()

    if snippet_id is not None:
        return db.session.query(db.exists().where(
            Snippet.snippet_id == snippet_id)).scalar()

def is_current_user_authenticated():
    return current_user.is_authenticated

def get_user(email=None,username=None,user_id=None):
    """
    Assumes that the user exists
    """
    if email is not None:
        return User.query.filter_by(email=email).first()

    if user_id is not None:
        return User.query.filter_by(user_id=user_id).first()

    if username is not None:
        return User.query.filter_by(username=username).first()


