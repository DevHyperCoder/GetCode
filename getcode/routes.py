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
from getcode import app
from getcode import db

from getcode import mail,bcrypt,login_manager
from getcode import MAINTANCE_MODE,PUBLIC,PRIVATE


def maintance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if MAINTANCE_MODE is True:
            return render_template('maintance.html')
        return f(*args, **kwargs)
    return decorated_function
  
@login_manager.user_loader
def     load_user(user_id):
    return User.query.get(user_id)

# sends a mail
def send_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',sender='arduinoleo88@gmail.com',
    recipients=[user.email])
    msg.body=f'''Hi {user.username},
    It seems you have requested a password reset request for {user.email}.
    To reset your password, please click on the link below or copy and paste the link in your browser
    {url_for('reset_password',token=token,_external=True)}
    If you didn't make this password reset request don't worry, nothing has been done to your account.
    '''
    mail.send(msg)

@app.route("/reset_password",methods=['get','post'])
def reset_request():
    if request.method=='POST':
        if current_user.is_authenticated:
            return redirect(url_for('profile'))
        email = request.form['email']
        email_exists = db.session.query(db.exists().where(
            User.email == email)).scalar()
        if email_exists:
            send_email(User.query.filter_by(email=email).first())
            return render_template("request_reset.html",success="An email has been sent to "+email)
        else:
            return render_template("request_reset.html",error="No users have registered with this email address")
            
    return render_template("request_reset.html")


@app.route("/reset_password/<token>",methods=['get','post'])
def reset_password(token):
    user = User.verifiy_reset_token(token)
    if user is None:
        return render_template('password_reset.html',user_error='Token has exipred or invalid token')
    if request.method=="POST":
        # handle post
        new_password = (request.form['password'])
        new_password_confirm = (request.form['chng-password'])

        if new_password == new_password_confirm:
            password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.password = password
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        if new_password != new_password_confirm:
            return render_template('password_reset.html',password_error = "Passwords don't match")



    return render_template("password_reset.html",token=token)


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



def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/google/login",methods=['get','post'])
def google_login():
    

    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/google/login/callback")
def callback():
    
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    #  Find out what URL to hit to get tokens that allow you to ask for
# things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))


    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        
        # Juicy part
        email_exists = db.session.query(db.exists().where(
                User.email == users_email)).scalar()
        
        if email_exists:
            # User log in
            user=User.query.filter_by(email=users_email).first()
            if user.google_login == GOOGLE_LOGIN:
                login_user(user,remember=True)
                return redirect(url_for('profile'))
            else:
                # TODO add a xustom screen
                return "LOGIN WITH PASSWORD"

        else:
            # TODO Research if you should log the user in
            user = User(email=users_email,
                        username=users_name,
                        password=bcrypt.generate_password_hash('getcode'),
                        google_login=GOOGLE_LOGIN)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('profile'))

    else:
        return "User email not available or not verified by Google.", 400


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("profile"))
    if request.method == "POST":
        user = db.session.query(db.exists().where(
            User.email == request.form['email'])).scalar()
        if user:
            user = User.query.filter_by(email=request.form['email']).first()
            password = request.form['password']
            if bcrypt.check_password_hash(user.password, password):
                # print(request.form['remember'])
                remember=False
                if 'remember'  in request.form:
                    remember = True
                login_user(user, remember=remember)  
                return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    if not current_user.is_authenticated:
        return redirect(url_for("home"))
    logout_user()
    return redirect(url_for("home"))

def does_user_exist(email=None, username=None):
    if email is not None:
        # Email is given
        return db.session.query(db.exists().where(
            User.email == email)).scalar()
    
    if username is not None:
        # Username is given
        return db.session.query(db.exists().where(
            User.username==username)).scalar()

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == 'POST':
        password = request.form['password']
        hashed_pass = bcrypt.generate_password_hash(password).decode('utf-8')
        username_exists = does_user_exist(username =  request.form['name'])
        if username_exists:
            print('u')
            return render_template("signup.html", username_error="Account exists")

        email_exists = does_user_exist(email= request.form['email'])
        if email_exists:
            print('e')
            return render_template("signup.html", email_eror="Account exists")

        user = User(username=request.form['name'],
                    email=request.form['email'], 
                    password=hashed_pass)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template("signup.html")


@app.route("/dashboard",methods=['GET','POST'])
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

        title_array = []
        description_array = []
        id_array = []

        for snippet in all_snippets:
            title_array.append(snippet.name)
            description_array.append(snippet.description)
            id_array.append(snippet.id)
        return render_template("dashboard.html", 
                                length=len(title_array),
                                id_array=id_array,
                                name_array=title_array, 
                                description_array=description_array)

    else:
        return redirect(url_for('login'))

# ---------------------------------------------------------------------------------------------------
# app
@app.route("/new/create", methods=['GET', 'POST'])
def create_new_snippet():
    
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        code = request.form['code']
        email = current_user.email
        created_date = date.today().strftime('%d/%m/%y')
        visibility = request.form['visibility']
        vis = PRIVATE
        if visibility == 'Public':
            vis = PUBLIC
        snippet = Snippet(name=title, 
        description=desc, email=email,
                          code=code, 
                          created_date=created_date,
                          likes=0,
                          comments='',
                          visibility = vis)
        db.session.add(snippet)
        db.session.commit()
    return render_template('new_snippet.html')
    

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

@app.route('/edit/<int:id>',methods=['GET','POST'])
def edit_snippet(id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    snipept = Snippet.query.filter_by(id=id).first()

    if request.method=='POST':
        
        visibility = request.form['visibility']
        vis = PRIVATE
        if visibility == 'Public':
            vis = PUBLIC
        
        snipept.name=request.form['title']
        snipept.description=request.form['desc']
        snipept.code=request.form['code']
        snipept.visibility=vis
        
        db.session.commit()

        return redirect(url_for('view',id=id))
    
    return render_template('new_snippet.html',
                            edit=True,
                            id=id,
                            snippet=snipept,
                            title=snipept.name,
                            desc=snipept.description,
                            code=snipept.code)


@app.route("/new/",methods=['get','post'])
def preview_new_snippet():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))   

    if not request.method == "POST":
        return render_template("new_snippet.html")

    return render_template('new_snippet.html',
                                title= request.form['title'] ,
                                desc = request.form['desc'],
                                code=request.form['code'])

@app.route('/delete/<int:id>',methods=['GET','POST','DELETE'])
def delete_snippet(id):
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    snippet  = Snippet.query.filter_by(id=id).first()

    if snippet.email != current_user.email:
        return 'not currecrt user or snippet'
    
    if request.method=='POST':
        print("GOING TO DELETE app")
        if request.form['name'] != snippet.name:
            return render_template('delete_snippet.html',id=snippet.id,name=snippet.name,error="E-NAME")
        db.session.delete(snippet)
        db.session.commit()


    return render_template('delete_snippet.html',id=snippet.id,name=snippet.name)


@app.route("/view/<int:id>",methods=['GET','POST'])
def view(id):
    snippet = Snippet.query.filter_by(id=id).first()
    
    if snippet.visibility==PUBLIC:
        if request.method=='POST':
            if current_user.is_authenticated == False:
                return render_template("view_snippet.html",id = snippet.id, title=snippet.name, desc=snippet.description, code=snippet.code,comment_error="lease log in inodred to psot a cometn")

            if 'comment_body' in request.form:
                comment=Comments.query.filter_by(comment=request.form['comment_body']).first()
                if comment is not None:
                    return render_template("view_snippet.html",id=snippet.id, title=snippet.name, desc=snippet.description, code=snippet.code,comment_error="can;'post same commetn")         
                comment = Comments(email_of_commenter=current_user.email,
                                   created_date=date.today().strftime('%d/%m/%y'),
                                   comment=request.form['comment_body'],post_name=snippet.name )
                db.session.add(comment)
                db.session.commit()
            
        comments = Comments.query.filter_by(post_name=snippet.name).all()
        if comments == None:
            if current_user.is_authenticated:
                return render_template("view_snippet.html",
                                        id=snippet.id,
                                        title=snippet.name,
                                        desc=snippet.description, 
                                        code=snippet.code)
        # Comments view
        usernames = []
        dates = []
        text=[]
        img=[]
        for comment_ in comments:
            dates.append(comment_.created_date)
            text.append(comment_.comment)
            email = comment_.email_of_commenter
            username = User.query.filter_by(email=email).first().username
            usernames.append((username))
            img.append('')
        
        return render_template("view_snippet.html", 
                                title=snippet.name,
                                id=snippet.id,
                                desc=snippet.description, 
                                code=snippet.code,
                                length = len(dates),
                                users=usernames,
                                comment = text,img=img,
                                created_date =dates)

    else:
        # private. check if the email is the curr user
        person =User.query.filter_by(email=snippet.email).first().username
        if request.method=='POST':
            if current_user.is_authenticated == False:
                return render_template("view_snippet.html", id=snippet.id , title=snippet.name, desc=snippet.description, code=snippet.code,comment_error="lease log in inodred to psot a cometn")
            if 'comment_body' in request.form:
                print("PRESENT")
                comment=Comments.query.filter_by(comment=request.form['comment_body']).first()
                if comment is not None:
                    return render_template("view_snippet.html", id=snippet.id, title=snippet.name, desc=snippet.description, code=snippet.code,comment_error="can;'post same commetn")         
                comment = Comments(email_of_commenter=current_user.email,
                                   created_date=date.today().strftime('%d/%m/%y'),
                                   comment=request.form['comment_body'],post_name=snippet.name )
                db.session.add(comment)
                db.session.commit()
        if  current_user.is_authenticated and current_user.email == snippet.email :
            comments = Comments.query.filter_by(post_name=snippet.name).all()
            if comments == None:
                if current_user.is_authenticated:
                    return render_template("view_snippet.html",
                    id=snippet.id,
                                            title=snippet.name,
                                            desc=snippet.description, 
                                            code=snippet.code)
            # Comments view
            usernames = []
            dates = []
            text=[]
            img=[]
            for comment_ in comments:
                dates.append(comment_.created_date)
                text.append(comment_.comment)
                email = comment_.email_of_commenter
                username = User.query.filter_by(email=email).first().username
                usernames.append((username))
                img.append('')
            
            return render_template("view_snippet.html", 
                                    title=snippet.name,
                                    id=snippet.id,
                                    desc=snippet.description, 
                                    code=snippet.code,
                                    length = len(dates),
                                    users=usernames,
                                    comment = text,img=img,
                                    created_date =dates)
        return render_template("view_snippet.html",error='Sorry! This is a private snippet by '+person)



@app.route('/settings',methods=['GET','POST'])
def settings():
    # TODO remove post if not necessary
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('settings.html',current_user_name=current_user.username)


@app.route('/like',methods=['get','post'])
def like_snippet():
    if request.method == 'POST':
        id=request.args.get('id', None)
        where = request.args.get('where','home')
        email = current_user.email
        
        if id is None:
            if where is "home":
                return redirect(url_for('home'))
            return redirect(url_for('profile'))
        snippet=Snippet.query.filter_by(id=id).first()
        snippet.likes = snippet.likes + 1
        
        
    
        old_liked = snippet.liked_users
        print(old_liked)
        if old_liked is not None and old_liked.__contains__(email):
            print("Already liked")
            if where is "home":
                return redirect(url_for('home'))
            return redirect(url_for('profile'))

        

        liked = ""
        if old_liked == "" or old_liked == None:
            # without comma
            liked = email
        else:
            string = ","+email
            liked = old_liked+string
        
        snippet.liked_users=liked

        db.session.add(snippet)
        db.session.commit()
        if where is "home":
            return redirect(url_for('home'))
        return redirect(url_for('profile'))
