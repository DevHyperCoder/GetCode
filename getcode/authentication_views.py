from flask import Blueprint


from getcode import login_manager,bcrypt
from getcode import db
from getcode.models import User

authentication_views = Blueprint('authentication_views',__name__)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@authentication_views.route("/google/login",methods=['get','post'])
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

@authentication_views.route("/google/login/callback")
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

@authentication_views.route("/login", methods=["GET", "POST"])
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

@authentication_views.route("/logout")
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
        return redirect(url_for('login'))

    return render_template("signup.html")



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

@authentication_views.route("/reset_password",methods=['get','post'])
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
            return redirect(url_for('login'))
        if new_password != new_password_confirm:
            return render_template('password_reset.html',password_error = "Passwords don't match")



    return render_template("password_reset.html",token=token)