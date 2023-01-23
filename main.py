
from flask import Flask, render_template, redirect, url_for, flash, abort, Response, request, session
from flask_bootstrap import Bootstrap
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import SignupForm, SigninForm
from webargs import flaskparser, fields
from functools import wraps
import validators
import re
import os
import os.path


def create_app(config_class=None):
    app = Flask(__name__)
    if config_class is None:
        app.config.from_object('config.DevelopmentConfig')
    else:
        app.config.from_object(config_class)
    app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    Bootstrap(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return Details.query.get(int(user_id))
    return app


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('sign_in'))

    return wrap


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('details.id'))


class Details(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(150))
    tasks = db.relationship('Todo', backref='user')


# with app.app_context():
#     db.create_all()


#     user_details = Details.query.filter_by(email='viney@gmail.com').first()
#     if user_details:
#         print("User already exists")
#     else:
#         user_details = Details(name='Divine', email='viney@gmail.com', password='kylianb')
#         db.session.add(user_details)
#         db.session.commit()
#         print("Added to the database")


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/sign-in', methods=["POST", "GET"])
def sign_in():
    errors = []
    if request.method == 'POST':
        email = request.form.get('email_address')
        password = request.form.get('password_input')
        if not email:
            errors.append('Email is required.')
        elif not validators.email(email):
            errors.append('Invalid email address.')
        if not password:
            errors.append('Password is required.')
        if not errors:
            user = Details.query.filter_by(email=email).first()
            if user:
                if check_password_hash(user.password, password):
                    login_user(user)
                    session['logged_in'] = True
                    return redirect(url_for('show_tasks'))
                else:
                    flash("Wrong password, try again.")
            else:
                flash("That user does not exist, try again.")

    return render_template("sign-in.html", errors=errors, logged_in=current_user.is_authenticated)


@app.route('/sign-up', methods=["POST", "GET"])
def sign_up():
    errors = []
    if request.method == 'POST':
        session['form_data'] = request.form
        user_name = session['form_data'].get('name_input')
        email = session['form_data'].get('email_address')
        password = session['form_data'].get('password_input')
        # pattern = re.compile("^(?=.*[A-Za-z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])[A-Za-z0-9!@#\$%\^&\*]{6,}$")
        confirm_password = session['form_data'].get('password_confirmation')
        if not user_name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
        elif not validators.email(email):
            errors.append('Invalid email address.')
        if not password:
            errors.append('Password is required.')
        elif not password == confirm_password:
            errors.append('Both passwords do not match.')
        # elif not pattern.match(password):
        #     errors.append("Password must contain at least six letters, one number and one symbol.")
        if not errors:
            user = Details.query.filter_by(email=email).first()
            if user:
                flash("You've already signed up with that email. Login instead.")
                return redirect(url_for("sign_in"))
            else:
                new_user = Details(name=user_name, email=email, password=generate_password_hash(password,
                                                                                                method='pbkdf2:sha256',
                                                                                                salt_length=8))
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                todo_list = Todo.query.all()
                return render_template("todo.html", todo_list=todo_list, name=user_name)
    return render_template("sign-up.html", errors=errors, session=session, logged_in=current_user.is_authenticated)


@app.route('/tasks', methods=["GET", "POST"])
@login_required
def show_tasks():
    if not current_user.is_authenticated:
        return redirect(url_for('sign_in'))
    todo_list = Todo.query.filter_by(user_id=current_user.id).all()
    name = session['form_data'].get('name_input')
    if request.method == "POST":
        return render_template('todo.html', todo_list=todo_list, name=name)
    return render_template("todo.html", todo_list=todo_list, name=name)


@app.route("/add", methods=["GET","POST"])
@login_required
def add_tasks():
    if not current_user.is_authenticated:
        return redirect(url_for('sign_in'))
    title = request.form.get("title")
    new_todo = Todo(title=title, complete=False, user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()
    return redirect(url_for("show_tasks"))


@app.route("/update/<int:todo_id>")
@login_required
def update(todo_id):
    if not current_user.is_authenticated:
        return redirect(url_for('sign_in'))
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for("show_tasks"))


@app.route("/delete/<int:todo_id>")
@login_required
def delete(todo_id):
    if not current_user.is_authenticated:
        return redirect(url_for('sign_in'))
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()
    todo.complete = not todo.complete
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("show_tasks"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)

