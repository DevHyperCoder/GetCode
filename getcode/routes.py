import traceback
from flask import render_template, request,url_for
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
                print(snippet.snippet_id)
        except:
            print("EXCEPTION")
            print(traceback.format_exc())

    title = []
    for i in show_snippet_array:
        title.append(i.name)
        print(i.name)
    

    return render_template("index.html",
                           snippet_array=show_snippet_array,
                           nav_params=nav_params)

@app.route("/about-us")
@maintance
def about_us():
    return render_template("about-us.html")

@app.route("/contact-us")
@maintance
def contact_us():
    return render_template("contact-us.html")


def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

# @app.route("/site-map")
# def site_map():
#     links = []
#     for rule in app.url_map.iter_rules():
#         # Filter out rules we can't navigate to in a browser
#         # and rules that require parameters
#         if "GET" in rule.methods and has_no_empty_params(rule):
#             url = url_for(rule.endpoint, **(rule.defaults or {}))
#             links.append((url, rule.endpoint))

#         if "POST" in rule.methods and has_no_empty_params(rule):
#             url = url_for(rule.endpoint, **(rule.defaults or {}))
#             links.append((url, rule.endpoint))
#     # links is now a list of url, endpoint tuples
#     return {"maps":links}


