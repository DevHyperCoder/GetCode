from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from getcode.models import User, Snippet
from getcode.routes import PUBLIC, PRIVATE
from getcode import db
import traceback
from datetime import date
from getcode.rand_id import get_rand_base64
from getcode.utils import does_snippet_exist

snippet_api = Blueprint('snippet_api', __name__)

# Return all snippets which are public


@snippet_api.route("/api/snippets/all")
def get_all_snippets():
    all_snippets = Snippet.query.all()

    show_snippet_array = []
    created_by_array = []
    title = []
    for snippet in all_snippets:
        try:

            if snippet.name is None or snippet.name is "":
                continue

            vis = snippet.visibility
            if vis == PUBLIC:
                show_snippet_array.append(snippet)

        except:
            print("EXCEPTION")
            print(traceback.format_exc())
            return {"error": "can't view all snippets"}

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

    json = request.get_json()

    if not user:
        return {"error": "No user found"}

    user_email = user.email

    snippet_title = json.get('title')

    # Check if the title exists before!

    if does_snippet_exist(snippet_title):
        return {"error":"Title exists"}

    snippet_desc = json.get('desc')
    snippet_code = json.get('code')
    visibility = json.get('visibility')
    created_date = date.today().strftime("%d/%m/%y")

    snippet_visibility = PRIVATE
    if visibility is "Public":
        snippet_visibility = PUBLIC

    # Generate Random ID
    snippet_id = get_rand_base64()

    snippet = Snippet(name=snippet_title,
                      description=snippet_desc,
                      code=snippet_code,
                      visibility=snippet_visibility,
                      email=user_email,
                      created_date=created_date,
                      likes=0,
                      comments='',
                      created_by_username=username,
                      snippet_id=snippet_id)

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

    return {"success": "Snippet has been delted for ever"}


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

    return {"success": "Snippet updated"}
