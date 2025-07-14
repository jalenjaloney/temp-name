from flask import Flask, render_template, url_for, flash, redirect, request
import git
from forms import RegistrationForm
from flask_behind_proxy import FlaskBehindProxy

from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
proxied = FlaskBehindProxy(app)  ## add this line

app.config['SECRET_KEY'] = '7669a686970f61dd6a2c7598628b864d'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

# class User(db.Model):
#   id = db.Column(db.Integer, primary_key=True)
#   username = db.Column(db.String(20), unique=True, nullable=False)
#   email = db.Column(db.String(120), unique=True, nullable=False)
#   password = db.Column(db.String(60), nullable=False)

#   def __repr__(self):
#     return f"User('{self.username}', '{self.email}')"

#CREATE USER / CATALOGUE / EPISODE / MODELS LIKE THIS IS YOU WANT

with app.app_context():
  db.create_all()


@app.route("/")
@app.route("/home")
def home():
    users = User.query.all()
    return render_template('home.html', subtitle='Home Page', text='This is the home page', users=users)


# @app.route("/sign_in")
# def second_page():
#     return render_template('about.html', subtitle='About Page', text='This is the about page')

# @app.route("/sign_up", methods=['GET', 'POST'])
# def register():
#     form = RegistrationForm()
#     if form.validate_on_submit(): # checks if entries are valid
#         user = User(username=form.username.data, email=form.email.data, password=form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         flash(f'Account created for {form.username.data}!', 'success')
#         return redirect(url_for('home')) # if so - send to home page
#     return render_template('register.html', title='Register', form=form)

# @app.route("/update_server", methods=['POST'])
# # def webhook():
# #     if request.method == 'POST':
# #         repo = git.Repo('/home/thealienseb/SEO_Flask_practice')
# #         origin = repo.remotes.origin
# #         origin.pull()
# #         return 'Updated PythonAnywhere successfully', 200
# #     else:
# #         return 'Wrong event type', 400

# # if __name__ == '__main__':
# #     app.run(debug=True, host="0.0.0.0")
