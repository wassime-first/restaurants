from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, URLField, BooleanField, SelectField
from wtforms.validators import DataRequired, URL, Email
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("URI")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
# basedir = os.path.abspath(os.path.dirname(__file__))
# database_path = os.path.join(basedir, '../second/instance/cafes.db')
# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_DATABASE_URI'] = URI
Bootstrap(app)


db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    __tablename__ = 'users_caffee'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(1000), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class UpdateCafe(FlaskForm):
    price = StringField("Price", validators=[DataRequired()])
    submit = SubmitField()

class LoginForm(FlaskForm):
    email = StringField("email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")

class AddCaffe(FlaskForm):
    calls = SelectField('Calls', choices=[('True', 'Yes'), ('False', 'No')])
    wifi = SelectField('Wifi', choices=[('True', 'Yes'), ('False', 'No')])
    sockets = SelectField('Sockets', choices=[('True', 'Yes'), ('False', 'No')])
    toilet = SelectField("Toilet", choices=[('True', 'Yes'), ('False', 'No')])
    img_url = URLField("Cafe Image URL", validators=[DataRequired(), URL()])
    map_url = URLField(
        'Cafe Location on Google Map',
        validators=[DataRequired(), URL()]
    )
    location = StringField("Location", validators=[DataRequired()])
    name = StringField("Cafe Name", validators=[DataRequired()])
    seats = StringField("Seats", validators=[DataRequired()])
    coffee_price = StringField("Coffee Price", validators=[DataRequired()])
    submit = SubmitField(
        'Add Cafe'
    )


@app.route('/')
def home():
    return render_template('index.html', looged_in=current_user.is_authenticated)


@app.route('/cafes')
def cafes():
    url = "https://cafe-api-q5vt.onrender.com/all"
    response = requests.get(url=url)
    all_cafes = response.json()
    keys = all_cafes[0].keys()
    return render_template('cafes.html', looged_in=current_user.is_authenticated, keys=keys, cafes=all_cafes)


@app.route('/add', methods=["POST", "GET"])
@login_required
def add():
    form = AddCaffe(
        coffee_price="$"
    )
    if form.validate_on_submit():
        url = "https://cafe-api-q5vt.onrender.com/add"
        params = {
            # "id": 30,
            "name": form.name.data,
            "map_url": form.map_url.data,
            "img_url": form.img_url.data,
            "location": form.location.data,
            "seats": form.seats.data,
            "has_toilet": form.toilet.data,
            "has_wifi": form.wifi.data,
            "has_sockets": form.sockets.data,
            "can_take_calls": form.calls.data,
            "coffee_price": form.coffee_price.data,
        }

        response = requests.post(url, data=params)
        response.raise_for_status()
        return redirect(url_for('home', looged_in=current_user.is_authenticated))

    return render_template('add.html', form=form, looged_in=current_user.is_authenticated)


@app.route("/update/<int:id>", methods=["POST", "GET"])
@login_required
def update(id):
    form = UpdateCafe()
    if form.validate_on_submit():
        n = form.price.data
        url = f"https://cafe-api-q5vt.onrender.com/patch/{1}/{n}"
        response = requests.patch(url=url)
        response.raise_for_status()
        return redirect(url_for('home'))
    return render_template('update.html', form=form, looged_in=current_user.is_authenticated)

@app.route("/delete/<int:id>")
@login_required
def delete(id):

    url = f"https://cafe-api-q5vt.onrender.com/delete/{id}"
    params = {
            "s": "12345678"
        }
    response = requests.delete(url=url, headers=params)
    response.raise_for_status()
    return redirect(url_for('home'))

@app.route("/register", methods=["POST","GET"])
def register():

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        new_user = User(email=email, password=generate_password_hash(password, salt_length=8))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template("register.html", form=form, looged_in=current_user.is_authenticated)

@app.route("/login", methods=["POST","GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.session.query(User).filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            return redirect(url_for('login'))
    return render_template("login.html", looged_in=current_user.is_authenticated, form=form)

@app.route("/logout", methods=["POST","GET"])
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5444)
