import sys
import traceback
from datetime import date
from flask import Flask, render_template, request, redirect, url_for,jsonify,g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required,UserMixin
from flask_bcrypt import Bcrypt
import os
from flask_mail import Mail,Message
from werkzeug.security import generate_password_hash, check_password_hash

import json
from functools import wraps

from oauthlib.oauth2 import WebApplicationClient
import requests

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer



PUBLIC = 1
PRIVATE =0
GOOGLE_LOGIN = 1
FACEBOOK_LOGIN = 2
GITHUB_LOGIN=3

MAINTANCE_MODE = os.environ.get('MAINTANCE_MODE')

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = "getcode"

# Configuration for Google Login
GOOGLE_CLIENT_ID = os.environ.get("CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

# BCRYPT Setup
bcrypt = Bcrypt(app)

# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)

# Databse config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
# Database initilisation
db = SQLAlchemy()

# Flask-Mail setup to use GMail
app.config['MAIL_SERVER']=os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT']=os.environ.get('MAIL_PORT')
app.config['MAIL_USE_TLS']=True
app.config['MAIL_USERNAME']=os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD']=os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

def maintance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if MAINTANCE_MODE is True:
            return render_template('maintance.html')
        return f(*args, **kwargs)
    return decorated_function
    

class User(db.Model, UserMixin):
    """Model for user accounts."""

    __tablename__ = 'users'

    id = db.Column(db.Integer,
                   primary_key=True)
    username = db.Column(db.String,
                         nullable=False,
                         unique=False)
    email = db.Column(db.String(40),
                      unique=True,
                      nullable=False)
    password = db.Column(db.String(200),
                         primary_key=False,
                         unique=False,
                         nullable=False)
    google_login=db.Column(db.Integer,unique=False,nullable=False)

    def get_reset_token(self,expires_sec=1800):
        # defualtis 30min
        s=Serializer(app.config['SECRET_KEY'],expires_sec)
        return s.dumps({"user_id": self.id}).decode('utf-8')

    @staticmethod
    def verifiy_reset_token(token):
        s=Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Snippet(db.Model):
    __tablename__ = 'code_snippets'
    __searchable__ =['name','description','code','email','tags']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.String, nullable=False, unique=False)
    email = db.Column(db.String(40),
                      unique=False,
                      nullable=False)
    code = db.Column(db.String, unique=False, nullable=False)
    created_date = db.Column(db.String, nullable=False, unique=False)
    likes = db.Column(db.Integer, primary_key=False,
                      nullable=False, unique=False)
    liked_users=db.Column(db.String,nullable = True,unique=False)
    comments = db.Column(db.String, nullable=True, unique=False)
    tags = db.Column(db.String,nullable=True,unique=False)
    visibility  =db.Column(db.Integer,nullable = True)

class Comments(db.Model):
    __tablename__='comments'
    id = db.Column(db.Integer, primary_key=True)
    email_of_commenter = db.Column(db.String(40),
                      unique=False,
                      nullable=False)
    created_date = db.Column(db.String, nullable=False, unique=False)
    comment = db.Column(db.String, nullable=False, unique=False)
    post_name = db.Column(db.String, nullable=False, unique=False)

db.init_app(app)

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
        title = request.form['title']
        desc = request.form['desc']
        code = request.form['code']
        visibility = request.form['visibility']
        vis = PRIVATE
        if visibility == 'Public':
            vis = PUBLIC
        
        snipept.name=title
        snipept.description=desc
        snipept.code=code
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
        print("GOING TO DELETE APP")
        if request.form['name'] != snippet.name:
            return render_template('delete_snippet.html',id=snippet.id,name=snippet.name,error="E-NAME")
        db.session.delete(snippet)
        db.session.commit()


    return render_template('delete_snippet.html',id=snippet.id,name=snippet.name)


@app.route("/view/<int:id>",methods=['GET','POST','DELETE'])
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


if __name__ == "__main__":
    # Comment out for migration NULL Value cant
    # migrate = Migrate(app,db)
    # manager = Manager(app)
    # manager.add_command('db',MigrateCommand)
    # manager.run()
    # print("MIGRATE")
    app.run(port=8080)
    
    
