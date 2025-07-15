from flask import Flask, render_template, url_for, flash, redirect, request
import git
from app.forms import RegistrationForm, LoginForm
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from app.models import db, User

app = Flask(__name__)
proxied = FlaskBehindProxy(app)

app.config['SECRET_KEY'] = '7669a686970f61dd6a2c7598628b864d'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' #redirects unathorized users
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#CREATE USER / CATALOGUE / EPISODE / MODELS LIKE THIS IS YOU WANT

with app.app_context():
  db.create_all()


@app.route("/")
@app.route("/home")
def home():
    users = User.query.all()
    return render_template('home.html', subtitle='Home Page', text='This is the home page', users=users)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit(): # checks if entry fulfills defined validators
        # creating user and adding to database
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login')) # send to login page after successful register
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
  form = LoginForm()
  if form.validate_on_submit():
      user = User.query.filter_by(username=form.username.data).first()
      print("Stored password:", user.password)
      print("Entered password:", form.password.data)
      if user and user.password == form.password.data:
         login_user(user, remember=form.remember.data)
         flash('Login successful!', 'success')
         return redirect(url_for('home'))
      else:
         form.username.errors.append('Invalid username or password.')
  return render_template("login.html", form=form)

# @app.route("/update_server", methods=['POST'])
# # def webhook():
# #     if request.method == 'POST':
# #         repo = git.Repo('/home/thealienseb/SEO_Flask_practice')
# #         origin = repo.remotes.origin
# #         origin.pull()
# #         return 'Updated PythonAnywhere successfully', 200
# #     else:
# #         return 'Wrong event type', 400