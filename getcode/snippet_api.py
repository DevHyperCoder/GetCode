from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from getcode.models import User, Snippet
from getcode.routes import PUBLIC, PRIVATE
from getcode import db
import traceback
from datetime import date

snippet_api = Blueprint('snippet_api', __name__)


@snippet_api.route("/api/snippets/all")
@jwt_required
def get_all_snippets():
    user = get_jwt_identity()

    all_snippets = Snippet.query.all()

    # We have the username of the user
    user_exists = db.session.query(
        db.exists().where(User.username == user)).scalar()
    if not user_exists:
        return {"error": "user doesn't exist"}

    usera = User.query.filter_by(username=user).first()
    email = usera.email

    show_snippet_array = []
    created_by_array = []
    title = []
    for snippet in all_snippets:
        try:

            if snippet.name is None or snippet.name is "":
                continue

            email = snippet.email
            email_exists = db.session.query(db.exists().where(
                User.email == email)).scalar()
            vis = snippet.visibility
            if vis == PUBLIC:
                show_snippet_array.append(snippet)

            if email_exists and vis == PRIVATE and email == usera.email:
                show_snippet_array.append(snippet)
                title.append(snippet.name)

        except:
            print("EXCEPTION")
            print(traceback.format_exc())
            return {"error": "can't view all snippets"}
    title = []
    for i in show_snippet_array:
        title.append(i.name)
        print(i.name)

    return {"snippets": [i.serialize for i in show_snippet_array]}


@snippet_api.route("/api/snippets/<id>")
@jwt_required
def get_snippet(id):
    username = get_jwt_identity()

    snippet = Snippet.query.filter_by(id=id).first()

    print(snippet)

    if not snippet:
        return {"error": "No snippet found"}

    if snippet.visibility == PUBLIC:
        return {"snippet": snippet.serialize}

    elif snippet.visibility == PRIVATE and snippet.created_by_username == username:
        return {"snippet": snippet.serialize}
    else:
        return {"error": "PRIVATE SNIPPET"}


@snippet_api.route("/api/snippets", methods=['POST'])
@jwt_required
def create_snippet():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()
    if not user:
        return {"error": "No user found"}
    user_email = user.email

    # TODO check if snippet exisits in the db

    snippet_title = request.form['title']
    snippet_desc = request.form['desc']
    snippet_code = request.form['code']
    visibility = request.form['visibility']
    created_date = date.today().strftime("%d/%m/%y")

    snippet_visibility = PRIVATE
    if visibility is "Public":
        snippet_visibility = PUBLIC

    snippet = Snippet(name=snippet_title,
                      description=snippet_desc,
                      code=snippet_code,
                      visibility=snippet_visibility,
                      email=user_email,
                      created_date=created_date,
                      likes=0,
                      comments='',
                      created_by_username=username)

    db.session.add(snippet)
    db.session.commit()

    return {"success": snippet_title}


@snippet_api.route("/api/snippets/<int:id>", methods=['DELETE'])
@jwt_required
def delete_snippet(id):
    username = get_jwt_identity()

    user = User.query.filter_by(username=username).first()

    if not user:
        return {"error": "No user found"}

    snippet = Snippet.query.filter_by(id=id).first()

    if not snippet:
        return {"error": "No snippet found"}

    if user.email != snippet.email:
        print("USER"+user.email)
        print("USERS"+snippet.email)
        return {"error": "Users dont match"}

    db.session.delete(snippet)
    db.session.commit()

    return {"success":"Snippet has been delted for ever"}


@snippet_api.route("/api/snippets/<int:id>", methods=['PATCH'])
@jwt_required
def edit_snippet(id):
    username = get_jwt_identity()

    user = User.query.filter_by(username=username).first()

    if not user:
        return {"error": "No user found"}

    snippet = Snippet.query.filter_by(id=id).first()

    if not snippet:
        return {"error": "No snippet found"}

    if user.email != snippet.email:
        return {"error": "Users dont match"}

    visibility = request.form['visibility']
    vis = PRIVATE
    if visibility == 'Public':
        vis = PUBLIC

    snippet.name = request.form['title']
    snippet.description = request.form['desc']
    snippet.code = request.form['code']
    snippet.visibility = vis

    db.session.commit()

    return {"success":"Snippet updated"}
