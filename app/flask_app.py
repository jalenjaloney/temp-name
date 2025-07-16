from flask import Flask, render_template, url_for, flash, redirect, request
import git
import requests
import pandas as pd
from flask_behind_proxy import FlaskBehindProxy
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from forms import RegistrationForm, LoginForm
from flask_behind_proxy import FlaskBehindProxy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
import sqlite3

app = Flask(__name__)
proxied = FlaskBehindProxy(app)

app.config['SECRET_KEY'] = 'SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

db.init_app(app)

BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' #redirects unathorized users
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
  db.create_all()

def fetch_popular(media_type="movie", pages=1):
    """Fetch multiple pages of popular movies or TV shows"""
    results = []
    for page in range(1, pages + 1):
        url = f"{BASE_URL}/{media_type}/popular"
        response = requests.get(url, params={"api_key": TMDB_API_KEY, "page": page})
        response.raise_for_status()
        results.extend(response.json()["results"])
    return results

def parse_tmdb_items(items, media_type):
    """Extract only the fields we care about"""
    parsed = []
    for item in items:
        parsed.append({
            "tmdb_id": item["id"],
            "title": item.get("title") or item.get("name"),
            "media_type": media_type,
            "poster_url": IMG_BASE_URL + item["poster_path"] if item.get("poster_path") else None,
            "overview": item.get("overview", ""),
            "release_date": item.get("release_date") or item.get("first_air_date"),
            "vote_average": item.get("vote_average"),
        })
    return parsed

def fetch_tv_seasons(tv_id):
    url = f"{BASE_URL}/tv/{tv_id}"
    response = requests.get(url, params={"api_key": TMDB_API_KEY})
    response.raise_for_status()
    return response.json().get("seasons", [])

def parse_seasons(tv_id, title, seasons_raw):
    seasons = []
    for season in seasons_raw:
        seasons.append({
            "season_id": f"{tv_id}-{season['season_number']}",
            "tv_id": tv_id,
            "title": title,
            "season_number": season["season_number"],
            "name": season.get("name"),
            "overview": season.get("overview"),
            "poster_url": IMG_BASE_URL + season["poster_path"] if season.get("poster_path") else None,
            "air_date": season.get("air_date"),
            "episode_count": season.get("episode_count"),
            "vote_average": season.get("vote_average"),
        })
    return seasons

def fetch_season_episodes(tv_id, season_number):
    url = f"{BASE_URL}/tv/{tv_id}/season/{season_number}"
    response = requests.get(url, params={"api_key": TMDB_API_KEY})
    response.raise_for_status()
    return response.json().get("episodes", [])

def parse_episodes(tv_id, season_num, season_id, episodes_raw):
    episodes = []
    for episode in episodes_raw:
        episodes.append({
            "episode_id": episode["id"],
            "season_id": season_id,
            "tv_id": tv_id,
            "season_number": season_num,
            "episode_number": episode["episode_number"],
            "episode_name": episode.get("name"),
            "overview": episode.get("overview"),
            "air_date": episode.get("air_date"),
            "runtime": episode.get("runtime"),
            "vote_average": episode.get("vote_average"),
            "still_url": IMG_BASE_URL + episode["still_path"] if episode.get("still_path") else None,
        })
    return episodes

# Fetch and parse both movies and TV shows
movies_raw = fetch_popular("movie", pages=2)
tv_raw = fetch_popular("tv", pages=2)

movies = parse_tmdb_items(movies_raw, "movie")
tv = parse_tmdb_items(tv_raw, "tv")

# Combine and store
df = pd.DataFrame(movies + tv)
df.to_csv("media_catalog.csv", index=False)
print("Saved media_catalog.csv with", len(df), "entries")

df = pd.read_csv('media_catalog.csv')
# Update TMDB to show to catalogue page
@app.route('/')
def catalogue():
    # Sends only the top 10 movies and tv shows to the catalogue page
    movies = df[df["media_type"] == "movie"].head(10).to_dict(orient='records')
    tv_shows = df[df["media_type"] == "tv"].head(10).to_dict(orient='records')
    users = User.query.all()
    return render_template('catalogue.html', movies=movies, tv_shows=tv_shows, users=users)

@app.route('/media/<media_id>')
def get_media(media_id):
    media = df[df["tmdb_id"] == int(media_id)].iloc[0].to_dict()
    # gets seasons
    seasons = []
    if media["media_type"] == "tv":
        conn = sqlite3.connect("media.db")
        season_query = f"SELECT * FROM seasons WHERE tv_id = '{media_id}' ORDER BY season_number"
        season_df = pd.read_sql(season_query, conn)

        for idx, row in season_df.iterrows():
            season_dict = row.to_dict()
            episode_query = f"SELECT * FROM episodes WHERE season_id = '{row['season_id']}' ORDER BY episode_number"
            episode_df = pd.read_sql(episode_query, conn)
            season_dict["episodes"] = episode_df.to_dict(orient="records") 

            seasons.append(season_dict)
        conn.close()
    return render_template('season_page.html', item=media, seasons=seasons)

# @app.route('/season/<season_id>')
# def view_season(season_id):
#     conn = sqlite3.connect("media.db")
#     season_query = f"SELECT * FROM seasons WHERE season_id = '{season_id}'"
#     season = pd.read_sql(season_query, conn).iloc[0].to_dict()

#     episodes_query = f"SELECT * FROM episodes WHERE season_id = '{season_id}' ORDER BY episode_number"
#     episodes = pd.read_sql(episodes_query, conn).to_dict(orient='records')
#     conn.close()

#     return render_template("season_detail.html", season=season, episodes=episodes)

@app.route('/episode/<int:episode_id>')
def view_episode(episode_id):
    conn = sqlite3.connect("media.db")
    episode_query = f"SELECT * FROM episodes WHERE episode_id = {episode_id}"
    episode = pd.read_sql(episode_query, conn).iloc[0].to_dict()
    conn.close()

    return render_template("episode_detail.html", episode=episode)

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
         return redirect(url_for('catalogue'))
      else:
         form.username.errors.append('Invalid username or password.')
  return render_template("login.html", form=form)

@app.route("/logout", methods=["GET", "POST"])
def logout():
   logout_user()
   return(redirect(url_for('login')))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")

# @app.route("/update_server", methods=['POST'])
# # def webhook():
# #     if request.method == 'POST':
# #         repo = git.Repo('/home/thealienseb/SEO_Flask_practice')
# #         origin = repo.remotes.origin
# #         origin.pull()
# #         return 'Updated PythonAnywhere successfully', 200
# #     else:
# #         return 'Wrong event type', 400
