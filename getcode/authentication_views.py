from flask import Blueprint,request,redirect,render_template,url_for
import requests
from flask_login import login_user,logout_user,current_user

from getcode import login_manager,bcrypt
from getcode import db,mail
from getcode.models import User
from getcode.utils import does_user_exist
from werkzeug.security import generate_password_hash, check_password_hash

from flask_mail import Message

authentication_views = Blueprint('authentication_views',__name__)

@authentication_views.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth_view.profile"))
    if request.method == "POST":
        user = db.session.query(db.exists().where(
            User.email == request.form['email'])).scalar()
        if user:
            user = User.query.filter_by(email=request.form['email']).first()
            password = request.form['password']
            if bcrypt.check_password_hash(user.password, password):
                remember=False
                if 'remember'  in request.form:
                    remember = True
                login_user(user, remember=remember)  
                return redirect(url_for("auth_view.profile"))
        return render_template('login.html',error='sdf')

    return render_template("login.html")

@authentication_views.route("/logout")
def logout():
    if not current_user.is_authenticated:
        return redirect(url_for("home"))
    logout_user()
    return redirect(url_for("home"))

@authentication_views.route("/signup", methods=['GET', 'POST'])
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
        return redirect(url_for('authentication_views.login'))

    return render_template("signup.html")



# sends a mail
def send_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',sender='arduinoleo88@gmail.com',
    recipients=[user.email])
    msg.body=f'''Hi {user.username},
    It seems you have requested a password reset request for {user.email}.
    To reset your password, please click on the link below or copy and paste the link in your browser
    {url_for('authentication_views.reset_password',token=token,_external=True)}
    If you didn't make this password reset request don't worry, nothing has been done to your account.
    '''
    mail.send(msg)

@authentication_views.route("/reset_password",methods=['get','post'])
def reset_request():
    if request.method=='POST':
        if current_user.is_authenticated:
            return redirect(url_for('auth_view.profile'))
        email = request.form['email']
        email_exists = db.session.query(db.exists().where(
            User.email == email)).scalar()
        if email_exists:
            send_email(User.query.filter_by(email=email).first())
            return render_template("request_reset.html",success="An email has been sent to "+email)
        else:
            return render_template("request_reset.html",error="No users have registered with this email address")
            
    return render_template("request_reset.html")


@authentication_views.route("/reset_password/<token>",methods=['get','post'])
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
            return redirect(url_for('authentication_views.login'))
        if new_password != new_password_confirm:
            return render_template('password_reset.html',password_error = "Passwords don't match")



    return render_template("password_reset.html",token=token)