import os
import sqlite3
import subprocess

import git
import pandas as pd
import requests
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_behind_proxy import FlaskBehindProxy
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from app.forms import RegistrationForm, LoginForm, commentForm
from app.google_ai import get_comments, summarize_comments
from app.models import Comment, User, db

app = Flask(__name__)
proxied = FlaskBehindProxy(app)

app.config["SECRET_KEY"] = "SECRET_KEY"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

db.init_app(app)

BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # redirects unathorized users
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


def fetch_popular(media_type="movie", pages=1):
    """Fetch multiple pages of popular movies or TV shows"""
    results = []
    for page in range(1, pages + 1):
        url = f"{BASE_URL}/{media_type}/popular"
        response = requests.get(
            url, params={"api_key": TMDB_API_KEY, "page": page})
        response.raise_for_status()
        results.extend(response.json()["results"])
    return results


def parse_tmdb_items(items, media_type):
    """Extract only the fields we care about"""
    parsed = []
    for item in items:
        parsed.append(
            {
                "tmdb_id": item["id"],
                "title": item.get("title") or item.get("name"),
                "media_type": media_type,
                "poster_url": (
                    IMG_BASE_URL + item["poster_path"]
                    if item.get("poster_path")
                    else None
                ),
                "overview": item.get("overview", ""),
                "release_date": item.get("release_date") or item.get("first_air_date"),
                "vote_average": item.get("vote_average"),
            }
        )
    return parsed


def fetch_tv_seasons(tv_id):
    url = f"{BASE_URL}/tv/{tv_id}"
    response = requests.get(url, params={"api_key": TMDB_API_KEY})
    response.raise_for_status()
    return response.json().get("seasons", [])


def parse_seasons(tv_id, title, seasons_raw):
    seasons = []
    for season in seasons_raw:
        seasons.append(
            {
                "season_id": f"{tv_id}-{season['season_number']}",
                "tv_id": tv_id,
                "title": title,
                "season_number": season["season_number"],
                "name": season.get("name"),
                "overview": season.get("overview"),
                "poster_url": (
                    IMG_BASE_URL + season["poster_path"]
                    if season.get("poster_path")
                    else None
                ),
                "air_date": season.get("air_date"),
                "episode_count": season.get("episode_count"),
                "vote_average": season.get("vote_average"),
            }
        )
    return seasons


def fetch_season_episodes(tv_id, season_number):
    url = f"{BASE_URL}/tv/{tv_id}/season/{season_number}"
    response = requests.get(url, params={"api_key": TMDB_API_KEY})
    response.raise_for_status()
    return response.json().get("episodes", [])


def parse_episodes(tv_id, season_num, season_id, episodes_raw):
    episodes = []
    for episode in episodes_raw:
        episodes.append(
            {
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
                "still_url": (
                    IMG_BASE_URL + episode["still_path"]
                    if episode.get("still_path")
                    else None
                ),
            }
        )
    return episodes


# Helper function to parse comment timestamp
def parse_timestamp_string(ts_str):
    parts = list(map(int, ts_str.split(":")))
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    else:
        raise ValueError("Invalid timestamp format")


# Fetch and parse both movies and TV shows
movies_raw = fetch_popular("movie", pages=2)
tv_raw = fetch_popular("tv", pages=2)

movies = parse_tmdb_items(movies_raw, "movie")
tv = parse_tmdb_items(tv_raw, "tv")

# Combine and store
df = pd.DataFrame(movies + tv)
df.to_csv("media_catalog.csv", index=False)
print("Saved media_catalog.csv with", len(df), "entries")

df = pd.read_csv("media_catalog.csv")


# Update TMDB to show to catalogue page
@app.route("/")
def catalogue():
    # Sends only the top 10 movies and tv shows to the catalogue page
    movies = df[df["media_type"] == "movie"].head(10).to_dict(orient="records")
    tv_shows = df[df["media_type"] == "tv"].head(10).to_dict(orient="records")
    users = User.query.all()
    return render_template(
        "catalogue.html", movies=movies, tv_shows=tv_shows, users=users
    )


@app.route("/media/<int:media_id>")
def get_media(media_id):
    media = df[df["tmdb_id"] == int(media_id)].iloc[0].to_dict()
    # gets seasons
    seasons = []
    if media["media_type"] == "tv":
        MEDIA_DB_PATH = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "media.db"
        )
        conn = sqlite3.connect(MEDIA_DB_PATH)
        season_query = (
            f"SELECT * FROM seasons WHERE tv_id = '{media_id}' ORDER BY season_number")
        season_df = pd.read_sql(season_query, conn)

        for idx, row in season_df.iterrows():
            season_dict = row.to_dict()
            episode_query = (
                f"SELECT * FROM episodes WHERE season_id = '{row['season_id']}' "
                "ORDER BY episode_number"
            )
            episode_df = pd.read_sql(episode_query, conn)
            season_dict["episodes"] = episode_df.to_dict(orient="records")

            seasons.append(season_dict)
        conn.close()
    return render_template("season_page.html", item=media, seasons=seasons)


# for movies
@app.route("/movie/<int:movie_id>", methods=["GET", "POST"])
def view_movie(movie_id):
    # get episode from sqlite
    MEDIA_DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "media.db"
    )
    conn = sqlite3.connect(MEDIA_DB_PATH)
    movie_query = (
        f"SELECT * FROM media WHERE tmdb_id = {movie_id} AND media_type = 'movie'")
    movie = pd.read_sql(movie_query, conn).iloc[0].to_dict()
    conn.close()

    # Allow commenting
    form = commentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        # Checking if timestamp is properly formatted
        try:
            timestamp_seconds = parse_timestamp_string(form.timestamp.data)
        except ValueError:
            flash("Invalid timestamp format.", "danger")
            return redirect(url_for("view_movie", movie_id=movie_id))

        new_comment = Comment(
            content=form.content.data,
            timestamp=timestamp_seconds,
            user_id=current_user.id,
            episode_id=int(movie_id),
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added!")
        return redirect(url_for("view_movie", movie_id=movie_id))

    comments = (
        Comment.query.filter_by(episode_id=int(movie_id))
        .order_by(Comment.timestamp)
        .all()
    )

    comment_block = get_comments(movie_id)
    emoji_summary = summarize_comments(comment_block) if comment_block else ""

    return render_template(
        "movie_page.html",
        movie=movie,
        form=form,
        comments=comments,
        emoji_summary=emoji_summary,
    )


# for shows
@app.route("/episode/<int:episode_id>", methods=["GET", "POST"])
def view_episode(episode_id):
    # get episode from sqlite
    MEDIA_DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "media.db"
    )
    conn = sqlite3.connect(MEDIA_DB_PATH)
    episode_query = f"SELECT * FROM episodes WHERE episode_id = {episode_id}"
    episode = pd.read_sql(episode_query, conn).iloc[0].to_dict()
    conn.close()

    # Allow commenting
    form = commentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        # Checking if timestamp is properly formatted
        try:
            timestamp_seconds = parse_timestamp_string(form.timestamp.data)
        except ValueError:
            flash("Invalid timestamp format.", "danger")
            return redirect(url_for("view_episode", episode_id=episode_id))

        new_comment = Comment(
            content=form.content.data,
            timestamp=timestamp_seconds,
            user_id=current_user.id,
            episode_id=int(episode_id),
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added!")
        return redirect(url_for("view_episode", episode_id=episode_id))

    comments = (
        Comment.query.filter_by(episode_id=int(episode_id))
        .order_by(Comment.timestamp)
        .all()
    )

    comment_block = get_comments(episode_id)
    emoji_summary = summarize_comments(comment_block) if comment_block else ""

    return render_template(
        "episode_page.html",
        episode=episode,
        form=form,
        comments=comments,
        emoji_summary=emoji_summary,
    )


@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != current_user.id:
        flash("You don't have permission to delete this comment.", "danger")
        return redirect(request.referrer or url_for("catalogue"))

    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "success")
    return redirect(request.referrer or url_for("catalogue"))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():  # checks if entry fulfills defined validators
        # creating user and adding to database
        user = User(username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {form.username.data}!", "success")
        return redirect(
            url_for("login")
        )  # send to login page after successful register
    return render_template("register.html", title="Register", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user, remember=form.remember.data)
                return redirect(url_for("catalogue"))
            else:
                form.password.errors.append("Invalid username or password.")
    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/update_server", methods=["POST"])
def webhook():
    if request.method == "POST":
        repo = git.Repo("/home/jalenseotechdev/stamper")
        origin = repo.remotes.origin
        origin.pull()

        # Rebuild media.db
        subprocess.run(["python3", "app/query_db.py"])

        return "Updated PythonAnywhere successfully", 200
    else:
        return "Wrong event type", 400


if __name__ == "__main__":
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
