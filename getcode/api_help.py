from flask import Blueprint,render_template

api_help = Blueprint('api_help',__name__)

@api_help.route("/api/help")
def help():
    return render_template("api-help.html")