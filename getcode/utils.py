from getcode import db
from getcode.models import User, Snippet


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
