import requests
import pandas as pd
from flask import Flask, render_template

TMDB_API_KEY = "4abd18d55b49ea191290f8344285d116"
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)

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

# Update TMDB to show to catalogue page
@app.route('/')
def catalogue():
    df = pd.read_csv('media_catalog.csv')
    # Sends only the top 10 movies and tv shows to the catalogue page
    movies = df[df["media_type"] == "movie"].head(10).to_dict(orient='records')
    tv_shows = df[df["media_type"] == "tv"].head(10).to_dict(orient='records')
    return render_template('catalogue.html', movies=movies, tv_shows=tv_shows)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
