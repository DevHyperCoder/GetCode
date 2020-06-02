from flask import Blueprint
from flask_jwt_extended import get_jwt_identity,jwt_required
from getcode.models import User,Snippet
from getcode.routes import PUBLIC,PRIVATE
from getcode import db

import traceback

snippet_api=Blueprint('snippet_api',__name__)

@snippet_api.route("/api/snippets/all")
@jwt_required
def get_all_snippets():
    user = get_jwt_identity()

    if not user:
        return{"error":"token invalid"}

    all_snippets=Snippet.query.all()
    print(user)

    # We have the username of the user
    user_exists = db.session.query(db.exists().where(User.username == user)).scalar()
    if not user_exists:
        return {"error":"user doesn't exist"}

    usera=User.query.filter_by(username=user).first()
    email=usera.email

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

            if email_exists and vis==PRIVATE and email==user.email:
                show_snippet_array.append(snippet)
                title.append(snippet.name)


        except:
            print("EXCEPTION")
            print(traceback.format_exc())
            return {"error":"can't view all snippets"}
    return {"snippets":show_snippet_array}

@snippet_api.route("/api/<token>/snippets/<id>")
def get_snippet(token,id):
    user = User.verifiy_reset_token(token)

    if not user:
        return{"error":"token invalid"}

    snippet = Snippet.query.filter_by(id=id).first()
    
    if snippet.visibility==PUBLIC:
        return {"snippet":snippet}

    elif snippet.visibility==PRIVATE and snippet.email==user.email:
        return {"snippet":snippet}
    else:
        return {"error":"PRIVATE SNIPPET"}