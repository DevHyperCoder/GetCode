from flask import Blueprint,redirect
from getcode import GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET,GOOGLE_LOGIN,GOOGLE_DISCOVERY_URL,db
from getcode.models import User

from flask_login import login_user

google_auth = Blueprint('google_auth',__name__)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@google_auth.route("/google/login",methods=['get','post'])
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

@google_auth.route("/google/login/callback")
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
                # TODO add a custom screen
                return "LOGIN WITH PASSWORD"

        else:
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
