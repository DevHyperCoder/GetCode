from flask import Blueprint


snippet_view = Blueprint('snippet_view','snippet_view')

@snippet_view.route('/asdf')
def asf():
    return "Blueprint didnt carasj!!"



