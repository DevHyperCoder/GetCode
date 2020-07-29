from flask import Blueprint, render_template, request
from getcode import PUBLIC
from flask_login import current_user
from getcode.models import User, Snippet
from getcode.utils import get_user, does_user_exist
user_view = Blueprint('user_view', __name__)


@user_view.route("/user/<string:id>")
def user_profile(id):
    user = User.query.filter_by(id=id).first()

    if not user:
        return render_template('user-profile.html', user_error='asdf')

    snippets_by_user = Snippet.query.filter_by(email=user.email).all()

    show_snippet_array = []
    for snippet in snippets_by_user:
        if snippet.visibility is PUBLIC:
            show_snippet_array.append(snippet)
        elif current_user.is_authenticated and snippet.email == current_user.email:
            show_snippet_array.append(snippet)

    return render_template('user-profile.html', user=user, snippet_array=show_snippet_array)


@user_view.route("/user")
def get_user_profile():
    user = None
    if 'username' in request.args:
        if does_user_exist(username=request.args['username']):
            user = get_user(username=request.args['username'])
    if 'user_id' in request.args:
        if does_user_exist(user_id=request.args['user_id']):
            user = get_user(user_id=request.args['user_id'])

    if 'email' in request.args:
        if does_user_exist(email=request.args['email']):
            user = get_user(email=request.args['email'])

    if not user:
        return render_template('user-profile.html', user_error='asdf')

    snippets_by_user = Snippet.query.filter_by(email=user.email).all()

    show_snippet_array = []
    for snippet in snippets_by_user:
        if snippet.visibility is PUBLIC:
            show_snippet_array.append(snippet)
        elif current_user.is_authenticated and snippet.email == current_user.email:
            show_snippet_array.append(snippet)

    return render_template('user-profile.html', user=user,snippet_array=show_snippet_array)
