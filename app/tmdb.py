import requests
import pandas as pd
from flask import Flask, render_template
import os
from dotenv import load_dotenv

load_dotenv()
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

# Update TMDB to show to catalogue page
@app.route('/')
def catalogue():
    df = pd.read_csv('media_catalog.csv')
    # Sends only the top 10 movies and tv shows to the catalogue page
    movies = df[df["media_type"] == "movie"].head(10).to_dict(orient='records')
    tv_shows = df[df["media_type"] == "tv"].head(10).to_dict(orient='records')
    return render_template('catalogue.html', movies=movies, tv_shows=tv_shows)

# fetch and parse tv show seasons
season_data = []
episode_data = []
for show in tv:
    tv_id = show["tmdb_id"]
    title = show["title"]

    seasons_raw = fetch_tv_seasons(tv_id)
    seasons = parse_seasons(tv_id, title, seasons_raw)
    season_data.extend(seasons)

    for season in seasons:
        season_num = season["season_number"]
        season_id = season["season_id"]

        episodes_raw = fetch_season_episodes(tv_id, season_num)
        episodes = parse_episodes(tv_id, season_num, season_id, episodes_raw)
        episode_data.extend(episodes)
    

season_df = pd.DataFrame(season_data)
season_df.to_csv("tv_seasons.csv", index=False)
print("Saved tv_seasons.csv with", len(season_df), "entries")

episode_df = pd.DataFrame(episode_data)
episode_df.to_csv("tv_episodes.csv", index=False)
print("Saved tv_episodes.csv with", len(episode_df), "entries")

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")