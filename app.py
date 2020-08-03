from flask import Flask, request, render_template, redirect, flash, session
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "some_secret_key"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

connect_db(app)


@app.route("/")
def home_page():
    """root url"""
    if "current_user" in session:
        """displays user page if already logged in"""
        return redirect(f"/users/{session['current_user']}")
    else: 
        """redirects to the register page"""
        return redirect("/register")


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if "current_user" in session:
        """displays user page if already logged in"""
        flash("You are already logged in", "info")
        return redirect("/")

    if form.validate_on_submit():
        """handles registration form"""
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(
            username, password, email, first_name, last_name)
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append("Username or Email already in use")
            return render_template("register.html", form=form)
        session["current_user"] = username
        flash(f"Successfuly registered", "success")
        return redirect(f"/users/{new_user.username}")

    else:
        """returns the register form page"""
        return render_template("register.html", form=form)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()
    if "current_user" in session:
        """displays user page if already logged in"""
        flash("You are already logged in", "info")
        return redirect("/")

    if form.validate_on_submit():
        """handles login form submission"""
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        if user:
            session["current_user"] = username
            flash(f"Successfuly logged in", "success")
            return redirect(f"/users/{username}")
        else:
            form.username.errors = ['Invalid username/password']
            return render_template("login.html", form=form)
    else:
        """returns login page"""
        return render_template("login.html", form=form)


@app.route("/users/<username>")
def secrets(username):
    if session['current_user']==username:
        """displays the current user page"""
        user=User.query.filter(User.username==username).first_or_404()
        feedback=Feedback.query.filter(Feedback.username==username)
        return render_template("user_home.html", user=user, feedback=feedback)
    else:
        """redirects to root url if username in url is not logged in"""
        flash("You do not have permission to view this page", "danger")
        return (redirect("/"), 401)


@app.route("/logout", methods=["POST"])
def logout():
    if "current_user" in session:
        """logs out a user"""
        session.pop("current_user")
        flash("Logged out", "info")
        return redirect("/")
    return redirect("/")

@app.route("/users/<username>/feedback/add", methods=["POST", "GET"])
def add_feedback(username):
    """a page to add feedback"""
    user=User.query.filter(User.username==username).first()
    if user.username==session['current_user']:
        form=FeedbackForm()
        if form.validate_on_submit():
            """handles feedback form"""
            title = form.title.data
            content = form.content.data
            feedback = Feedback(title=title, content=content, username=username)
            db.session.add(feedback)
            db.session.commit()
            return redirect(f"/users/{username}")
        else:
            """returns feedback from page"""
            return render_template("add_feedback.html", username=username, form=form)
    else:
        """redirects to root url"""
        flash("Please register or login", "danger")
        return redirect("/")

@app.route("/feedback/<int:id>/update", methods=["POST", "GET"])
def update_feedback(id):
    """a page to update feedback"""
    feedback=Feedback.query.get_or_404(id)
    if feedback.username==session['current_user']:
        form=FeedbackForm(obj=feedback)
        if form.validate_on_submit():
            """handles update form submission"""
            title = form.title.data
            content = form.content.data
            feedback.title=title
            feedback.content=content
            db.session.add(feedback)
            db.session.commit()
            return redirect(f"/users/{feedback.username}")
        else:
            return render_template("update_feedback.html", form=form, feedback=feedback)
    else:
        """redirects to root url"""
        flash("Please register or login", "danger")
        return redirect("/")

@app.route("/feedback/<int:id>/delete", methods=["POST"])
def delete(id):
    """deletes a feedback"""
    feedback=Feedback.query.get_or_404(id)
    if feedback.username==session['current_user']:
        db.session.delete(feedback)
        db.session.commit()
        flash("Deleted", "info")
        return redirect(f"/users/{feedback.username}")
    
    else:
        """redirects to root url"""
        flash("Please register or login", "danger")
        return redirect("/")