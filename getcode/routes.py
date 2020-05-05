import sys
import traceback
from datetime import date
from flask import render_template, request, redirect, url_for,jsonify,g
from flask_login import  login_user, logout_user, current_user, login_required,UserMixin
import os

from werkzeug.security import generate_password_hash, check_password_hash

import json
from functools import wraps

import requests

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

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
    created_by_array = []

    if len(all_snippets) < 1:
        # Empty
        return render_template('index.html',nav_params=nav_params,empty=True)

    for snippet in all_snippets:
        try:
            
            if snippet.name is None or snippet.name is "":
                continue

            email = snippet.email
            email_exists = db.session.query(db.exists().where(
                User.email == email)).scalar()
            vis = snippet.visibility
            if email_exists and vis == PUBLIC:
                user = User.query.filter_by(email=email).first()
                username = user.username
                created_by_array.append(username)
                show_snippet_array.append(snippet)


        except:
            print("EXCEPTION")
            print(traceback.format_exc())

    return render_template("index.html",
                           snippet_array=show_snippet_array,
                           created_by_array=created_by_array, 
                           nav_params=nav_params)








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







