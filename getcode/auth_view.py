from flask import Blueprint,request,render_template,redirect,url_for
from getcode.models import Snippet
from getcode import app,db
from flask_login import current_user 

from flask_jwt_extended import create_access_token

import datetime

auth_view= Blueprint('auth_view',__name__)

# Profile view and settings

@auth_view.route("/settings/access-token",methods=['POST'])
def access_token():
    if not current_user.is_authenticated:
        return redirect(url_for('authentication_views.login'))
    
    user = current_user
    
    access_token = create_access_token(identity=user.username,expires_delta=app.config['EXPIRY_DELTA'])
    return render_template('access_token_view.html',access_token=access_token)
    


@auth_view.route("/dashboard",methods=['GET','POST'])
def profile():
    if current_user.is_authenticated:
        current_user_email = current_user.email

        all_snippets =[]
        # TODO better search algorithm find out
        if 'search'  not in request.args:
            all_snippets=Snippet.query.filter_by(email=current_user_email).all()

        else:
            search_query = request.args['search']
            all_snippets_temp=Snippet.query.filter_by(email=current_user_email).all()
            for snippet in all_snippets_temp:
                if search_query in snippet.name:
                    print(snippet.name)
                    all_snippets.append(snippet)

        if len(all_snippets) is None or len(all_snippets) is 0:
            return render_template("dashboard.html", empty=True, length=0, snippets=[0])

        show_snippet_array=[]

        for snippet in all_snippets:
            show_snippet_array.append(snippet)

        return render_template("dashboard.html", 
                                snippet_array=show_snippet_array)

    else:
        return redirect(url_for('authentication_views.login'))

@auth_view.route('/settings',methods=['GET','POST'])
def settings():
    if not current_user.is_authenticated:
        return redirect(url_for('authentication_views.login'))

    if request.method=="POST":
        username=request.form['username']
        bio=request.form['bio']

        current_user.username=username
        current_user.bio=bio

        db.session.add(current_user)
        db.session.commit()

    return render_template('settings.html')