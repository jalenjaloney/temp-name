import os
import sqlite3
import subprocess

import git
import pandas as pd
import requests
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for, jsonify
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify, abort
from flask_behind_proxy import FlaskBehindProxy
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
# import all functions from tmdb.py except for generate_episode_csvs()
from app.tmdb import (
    fetch_popular,
    parse_tmdb_items,
    fetch_tv_seasons,
    parse_seasons,
    fetch_season_episodes,
    parse_episodes,
)
# import functions for anilist
from app.anilist import (
    fetch_anime,
    format_start_date,
    parse_anime,
    fetch_episodes,
    parse_episodes,
    extract_ep_num,
)

from app.forms import RegistrationForm, LoginForm, commentForm
from app.google_ai import get_comments, summarize_comments

from app.models import Comment, User, db
from app.tenor import search_gif, featured_gifs
from app.cache_tmdb import fetch_and_cache_movie, fetch_and_cache_show

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


# Update TMDB to show to catalogue page
@app.route("/")
def catalogue():
    MEDIA_DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "media.db"
    )
    conn = sqlite3.connect(MEDIA_DB_PATH)

    movie_query = "SELECT * FROM media WHERE media_type = 'movie' ORDER BY vote_average DESC LIMIT 50"
    tv_query = "SELECT * FROM media WHERE media_type = 'tv' ORDER BY vote_average DESC LIMIT 10"
    anime_query = "SELECT * FROM anime ORDER BY trending DESC LIMIT 10"

    movies = pd.read_sql(movie_query, conn).to_dict(orient="records")
    tv_shows = pd.read_sql(tv_query, conn).to_dict(orient="records")
    anime = pd.read_sql(anime_query, conn).to_dict(orient="records")

    conn.close()

    users = User.query.all()
    return render_template(
        "catalogue.html", movies=movies, tv_shows=tv_shows, anime=anime, users=users
    )



@app.route("/media/<int:media_id>")
def get_media(media_id):
    MEDIA_DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "media.db"
    )
    conn = sqlite3.connect(MEDIA_DB_PATH)
    
    # START OF SHOW LIVE QUERY
    # Check if media exists in our database
    media_query = f"SELECT * FROM media WHERE tmdb_id = {media_id}"
    media_df = pd.read_sql(media_query, conn)
    
    # If media doesn't exist, fetch and cache it
    if media_df.empty:
        try:
            fetch_and_cache_show(media_id, conn)
        except Exception as e:
            # If it fails as a TV show, it might be a movie that got here somehow
            try:
                fetch_and_cache_movie(media_id, conn)
            except Exception as e2:
                conn.close()
                abort(404)
        
        media_df = pd.read_sql(media_query, conn)
    
    if media_df.empty:
        conn.close()
        abort(404)
    
    media = media_df.iloc[0].to_dict()    # gets seasons

    MEDIA_DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "media.db"
    )
    conn = sqlite3.connect(MEDIA_DB_PATH)
    media_query = f"SELECT * FROM media WHERE tmdb_id = {media_id}"
    media = pd.read_sql(media_query, conn).iloc[0].to_dict()

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

    movie_query = f"SELECT * FROM media WHERE tmdb_id = {movie_id} AND media_type = 'movie'"
    media_df = pd.read_sql(movie_query, conn)

    #THIS IS WHERE THE NEW LIVE QUERY IS DONE
    # Check if movie exists in DB, and fetch if not
    if media_df.empty:
        try:
            fetch_and_cache_movie(movie_id, conn)
        except Exception as e:
            conn.close()
            abort(404)

        media_df = pd.read_sql(movie_query, conn)

    if media_df.empty:
        conn.close()
        abort(404)

    movie = media_df.iloc[0].to_dict()
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
            gif_url=form.gif_url.data
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
        "media_page.html",
        media=movie,
        media_type="movie",
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
            gif_url = form.gif_url.data,
            episode_id=int(episode_id)
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
        "media_page.html",
        media=episode,
        media_type="episode",
        form=form,
        comments=comments,
        emoji_summary=emoji_summary,
    )

# anime
@app.route("/anime/<int:anime_id>")
def view_anime(anime_id):
    MEDIA_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "media.db")
    conn = sqlite3.connect(MEDIA_DB_PATH)

    anime_query = f"SELECT * FROM anime WHERE anilist_id = {anime_id}"
    anime_result = pd.read_sql(anime_query, conn).to_dict(orient="records")
    if not anime_result:
        abort(404)
    anime = anime_result[0]

    episode_query = f"SELECT * FROM anime_ep WHERE anilist_id = {anime_id}"
    episodes = pd.read_sql(episode_query, conn).to_dict(orient="records")
    conn.close()

    # get episode nums
    episodes.sort(key=lambda x: extract_ep_num(x.get('episode_title')), reverse=False)

    return render_template("anime_page.html", anime=anime, episodes=episodes)

# anime details
@app.route("/aniepisode/<int:episode_id>", methods=["GET", "POST"])
def view_anime_episode(episode_id):
    MEDIA_DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "media.db"
    )
    conn = sqlite3.connect(MEDIA_DB_PATH)

    episode_query = f"SELECT * FROM anime_ep WHERE episode_id = {episode_id}"
    episode_df = pd.read_sql(episode_query, conn)
    

    if episode_df.empty:
        abort(404)

    episode = episode_df.iloc[0].to_dict()

    anilist_id = episode.get("anilist_id") # Get the anilist_id from the episode data
    anime_details = None
    if anilist_id:
        anime_query = f"SELECT * FROM anime WHERE anilist_id = {anilist_id}"
        anime_df = pd.read_sql(anime_query, conn)
        if not anime_df.empty:
            anime_details = anime_df.iloc[0].to_dict()
    conn.close()

    # Allow commenting
    form = commentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        try:
            timestamp_seconds = parse_timestamp_string(form.timestamp.data)
        except ValueError:
            flash("Invalid timestamp format.", "danger")
            return redirect(url_for("view_anime_episode", episode_id=episode_id))

        new_comment = Comment(
            content=form.content.data,
            timestamp=timestamp_seconds,
            gif_url=form.gif_url.data,
            user_id=current_user.id,
            episode_id=int(episode_id),
        )
        db.session.add(new_comment)
        db.session.commit()
        flash("Comment added!")
        return redirect(url_for("view_anime_episode", episode_id=episode_id))

    comments = (
        Comment.query.filter_by(episode_id=int(episode_id))
        .order_by(Comment.timestamp)
        .all()
    )

    comment_block = get_comments(episode_id)
    emoji_summary = summarize_comments(comment_block) if comment_block else ""

    return render_template(
        "media_page.html",
        media=episode,
        anime=anime_details,
        media_type="anime_episode",
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

@app.route("/search_gifs")
def search_gifs():
    query = request.args.get("q")
    pos = request.args.get("pos")
    limit = int(request.args.get("limit", 20))

    gifs = search_gif(query, limit=limit, pos=pos)
    
    # Convert to JSON response for Javascript in html
    return jsonify(gifs)

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 10)), 50)

    if not q:
        return jsonify([])

    # Step 1: Check local SQLite DB
    MEDIA_DB_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "media.db"
    )
    conn = sqlite3.connect(MEDIA_DB_PATH)
    cursor = conn.execute(
        """
        SELECT tmdb_id, title, overview, media_type, poster_url
        FROM media 
        WHERE title LIKE ? 
        ORDER BY title ASC 
        LIMIT ?
        """,
        (f"%{q}%", limit)
    )
    results = cursor.fetchall()
    conn.close()

    if results:
        # Format DB results
        return jsonify([
            {
                "id": row[0],
                "title": row[1],
                "description": row[2] or "",
                "media_type": row[3],
                "poster_url": row[4] or ""
            }
            for row in results
        ])

    # Step 2: Fallback to TMDB if no local matches
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    url = f"https://api.themoviedb.org/3/search/multi"
    res = requests.get(url, params={
        "api_key": TMDB_API_KEY,
        "query": q,
        "include_adult": False,
        "page": 1
    })

    if not res.ok:
        return jsonify([])

    data = res.json().get("results", [])[:limit]
    formatted = []

    for item in data:
        media_type = item.get("media_type")
        if media_type not in ["movie", "tv"]:
            continue

        title = item.get("title") or item.get("name") or ""
        poster_url = f"https://image.tmdb.org/t/p/w200{item['poster_path']}" if item.get("poster_path") else ""

        formatted.append({
            "id": item["id"],
            "title": title,
            "description": item.get("overview", ""),
            "media_type": media_type,
            "poster_url": poster_url
        })

    return jsonify(formatted)


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
        subprocess.run(["python3", "app/daily_update.py"])

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
