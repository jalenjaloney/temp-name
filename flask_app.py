from flask import Flask, render_template, url_for, flash, redirect, request
import git
import requests
import pandas as pd
# from forms import RegistrationForm
from flask_behind_proxy import FlaskBehindProxy
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
proxied = FlaskBehindProxy(app)  ## add this line

app.config['SECRET_KEY'] = '7669a686970f61dd6a2c7598628b864d'
TMDB_API_KEY = "4abd18d55b49ea191290f8344285d116"
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

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
media = df.to_dict(orient='records')
# Update TMDB to show to catalogue page
@app.route('/')
def catalogue():
    return render_template('catalogue.html', media=media)


#Dynamic routes for the specific show
@app.route("/media/<media_id>")
def handleShow(media_id):
  for item in media:
    if item['tmdb_id'] == int(media_id):
      return render_template('season_page.html',item=item)
  return render_template('season_page.html',item=None)



# @app.route("/update_server", methods=['POST'])
# # def webhook():
# #     if request.method == 'POST':
# #         repo = git.Repo('/home/thealienseb/SEO_Flask_practice')
# #         origin = repo.remotes.origin
# #         origin.pull()
# #         return 'Updated PythonAnywhere successfully', 200
# #     else:
# #         return 'Wrong event type', 400

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
