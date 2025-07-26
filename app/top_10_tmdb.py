import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"

def fetch_popular(media_type="movie", count=10):
    url = f"{BASE_URL}/{media_type}/popular"
    response = requests.get(url, params={"api_key": TMDB_API_KEY, "page": 1})
    response.raise_for_status()
    return response.json()["results"][:count]

def get_details(media_type, tmdb_id):
    url = f"{BASE_URL}/{media_type}/{tmdb_id}"
    response = requests.get(url, params={"api_key": TMDB_API_KEY})
    response.raise_for_status()
    return response.json()

def fetch_tv_seasons(tv_id):
    url = f"{BASE_URL}/tv/{tv_id}"
    response = requests.get(url, params={"api_key": TMDB_API_KEY})
    response.raise_for_status()
    return response.json().get("seasons", [])

def fetch_season_episodes(tv_id, season_number):
    url = f"{BASE_URL}/tv/{tv_id}/season/{season_number}"
    response = requests.get(url, params={"api_key": TMDB_API_KEY})
    response.raise_for_status()
    return response.json().get("episodes", [])

def parse_media(items, media_type):
    parsed = []
    for item in items:
        details = get_details(media_type, item["id"])
        parsed.append({
            "tmdb_id": item["id"],
            "title": item.get("title") or item.get("name"),
            "media_type": media_type,
            "poster_url": IMG_BASE_URL + item["poster_path"] if item.get("poster_path") else None,
            "overview": item.get("overview", ""),
            "release_date": item.get("release_date") or item.get("first_air_date"),
            "runtime": details.get("runtime") if media_type == "movie" else None,
            "vote_average": item.get("vote_average"),
        })
    return parsed

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

def parse_episodes(tv_id, season_num, season_id, episodes_raw):
    episodes = []
    for ep in episodes_raw:
        episodes.append({
            "episode_id": ep["id"],
            "season_id": season_id,
            "tv_id": tv_id,
            "season_number": season_num,
            "episode_number": ep["episode_number"],
            "episode_name": ep.get("name"),
            "overview": ep.get("overview"),
            "air_date": ep.get("air_date"),
            "runtime": ep.get("runtime"),
            "vote_average": ep.get("vote_average"),
            "still_url": IMG_BASE_URL + ep["still_path"] if ep.get("still_path") else None,
        })
    return episodes

# CHANGE THE FILE NAMES IN QUERY_DB TO CORRESPONDING TOP .CSV FILES TO GET ONLY THE TOP 10
def main():
    # Get top 10 movies and TV shows
    movies_raw = fetch_popular("movie", 10)
    tv_raw = fetch_popular("tv", 10)

    # Parse movie and TV metadata
    movies = parse_media(movies_raw, "movie")
    tv_shows = parse_media(tv_raw, "tv")

    # Save movies and shows
    media_df = pd.DataFrame(movies + tv_shows)
    media_df.to_csv("top_media.csv", index=False)
    print(f"Saved {len(media_df)} media items to top_media.csv")

    # Parse seasons and episodes for TV
    all_seasons = []
    all_episodes = []

    for show in tv_shows:
        tv_id = show["tmdb_id"]
        title = show["title"]

        seasons_raw = fetch_tv_seasons(tv_id)
        seasons = parse_seasons(tv_id, title, seasons_raw)
        all_seasons.extend(seasons)

        for season in seasons:
            season_num = season["season_number"]
            season_id = season["season_id"]

            episodes_raw = fetch_season_episodes(tv_id, season_num)
            episodes = parse_episodes(tv_id, season_num, season_id, episodes_raw)
            all_episodes.extend(episodes)

    pd.DataFrame(all_seasons).to_csv("top_tv_seasons.csv", index=False)
    print(f"Saved {len(all_seasons)} seasons to top_tv_seasons.csv")

    pd.DataFrame(all_episodes).to_csv("top_tv_episodes.csv", index=False)
    print(f"Saved {len(all_episodes)} episodes to top_tv_episodes.csv")

if __name__ == "__main__":
    main()
