import traceback
from flask import render_template, request
from flask_login import current_user

from functools import wraps

from getcode.models import User,Comments,Snippet
from getcode import app,db
from getcode import mail,bcrypt,login_manager
from getcode import MAINTANCE_MODE,PUBLIC,PRIVATE


def maintance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if MAINTANCE_MODE is True:
            return render_template('maintance.html')
        return f(*args, **kwargs)
    return decorated_function

@app.route("/",methods=['GET','POST'])
@maintance
def home():
    # print(app.config['SQLALCHEMY_DATABASE_URI'])
    # db.create_all()
    nav_params = current_user.is_authenticated
   
                
    
    all_snippets =[]
    # TODO better search algorithm find out
    if 'search'  not in request.args:
        all_snippets=Snippet.query.all()
    else:
        search_query = request.args['search']
        all_snippets_temp=Snippet.query.all()
        for snippet in all_snippets_temp:
            if search_query in snippet.name:
                print(snippet.name)
                all_snippets.append(snippet)

    show_snippet_array = []

    if len(all_snippets) < 1:
        # Empty
        return render_template('index.html',nav_params=nav_params,empty=True)

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

    return render_template("index.html",
                           snippet_array=show_snippet_array,
                           nav_params=nav_params)

@app.route("/about-us")
@maintance
def about_us():
    # TODO add a about us page
    return "About Us"

@app.route("/contact-us")
@maintance
def contact_us():
    # TODO add a contact us page
    return "Contact Us"






# ---------------------------------------------------------------------------------------------------
# app

    

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }
   
def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)







