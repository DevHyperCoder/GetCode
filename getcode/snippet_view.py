from flask import Blueprint,request,render_template,url_for,redirect
from datetime import date
from getcode.models import Snippet,User,Comments
from getcode import PUBLIC,PRIVATE

from flask_login import current_user

from getcode import db

snippet_view = Blueprint('snippet_view',__name__)

@snippet_view.route("/view/<int:id>",methods=['GET','POST'])
def view(id):
    snippet = Snippet.query.filter_by(id=id).first()
    
    # TODO Maybe refactor this to make it more readable
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
        if comments is None and current_user.is_authenticated:
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
                                comment = text,
                                img=img,
                                created_date =dates)

    else:
        # private. check if the email is the curr user
        person =User.query.filter_by(email=snippet.email).first().username
        if request.method=='POST':
            if current_user.is_authenticated == False:
                return render_template("view_snippet.html", id=snippet.id , title=snippet.name, desc=snippet.description, code=snippet.code,comment_error="lease log in inodred to psot a cometn")
            if 'comment_body' in request.form:
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

@snippet_view.route('/edit/<int:id>',methods=['GET','POST'])
def edit_snippet(id):
    if not current_user.is_authenticated:
        return redirect(url_for('authentication_views.login'))
    
    snipept = Snippet.query.filter_by(id=id).first()
    if snipept.email != current_user.email:
        # Return a nice error message
        return render_template('new_snippet.html',
                            edit=True,
                            id=id,
                            snippet=snipept,
                            title=snipept.name,
                            desc=snipept.description,
                            code=snipept.code,email_error='sadf')
    if request.method=='POST':
        i
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

@snippet_view.route("/new/",methods=['get','post'])
def preview_new_snippet():
    if not current_user.is_authenticated:
        return redirect(url_for('authentication_views.login'))   

    if not request.method == "POST":
        return render_template("new_snippet.html")

        # public iin seslect
    print(request.form['visibility'])
    if request.form['visibility'] == 'Public':
        return render_template('new_snippet.html',
                                title= request.form['title'] ,
                                desc = request.form['desc'],
                                code=request.form['code'],
                                public='sdf'
                                )



    return render_template('new_snippet.html',
                                title= request.form['title'] ,
                                desc = request.form['desc'],
                                code=request.form['code'],
                                private='asdf'
                                )

@snippet_view.route('/delete/<int:id>',methods=['GET','POST'])
def delete_snippet(id):
    if not current_user.is_authenticated:
        return redirect(url_for('authentication_views.login'))

    snippet  = Snippet.query.filter_by(id=id).first()

    if snippet.email != current_user.email:
        # Return a nice error message
        return render_template('delete_snippet.html',email_error='user')
    
    if request.method=='POST':
        if request.form['name'] != snippet.name:
            return render_template('delete_snippet.html',id=snippet.id,name=snippet.name,error="E-NAME")
        db.session.delete(snippet)
        db.session.commit()


    return render_template('delete_snippet.html',id=snippet.id,name=snippet.name)

@snippet_view.route('/like',methods=['post'])
def like_snippet():
    
    if not current_user.is_authenticated:
        where = request.args.get('where','home')
        if where is "home":
                return redirect(url_for('home'))
        return redirect(url_for('auth_view.profile')) 
    if request.method == 'POST':
        id=request.args.get('id', None)
        where = request.args.get('where','home')
        email = current_user.email
        print(where)
        if id is None:
            if where is "home":
                return redirect(url_for('home'))
            return redirect(url_for('auth_view.profile'))
        snippet=Snippet.query.filter_by(id=id).first()
        snippet.likes = snippet.likes + 1
        
        
    
        old_liked = snippet.liked_users
        print(old_liked)
        if old_liked is not None and old_liked.__contains__(email):
            print("Already liked")
            if where is "home":
                return redirect(url_for('home'))
            return redirect(url_for('auth_view.profile'))

        

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
        return redirect(url_for('auth_view.profile'))

@snippet_view.route("/new/create", methods=['GET', 'POST'])
def create_new_snippet():
    
    if not current_user.is_authenticated:
        return redirect(url_for('authentication_views.login'))

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