import os
import sqlite3
import requests
from dotenv import load_dotenv

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE_URL = "https://image.tmdb.org/t/p/w500"


def fetch_and_cache_movie(tmdb_id, conn):
    url = f"{BASE_URL}/movie/{tmdb_id}"
    response = requests.get(url, params={"api_key": TMDB_API_KEY})
    response.raise_for_status()
    data = response.json()
    
    entry = (
        data["id"],
        data.get("title"),
        "movie",
        IMG_BASE_URL + data["poster_path"] if data.get("poster_path") else None,
        data.get("overview"),
        data.get("release_date"),
        data.get("runtime"),
        data.get("vote_average"),
    )
    
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR IGNORE INTO media (
            tmdb_id, title, media_type, poster_url,
            overview, release_date, runtime, vote_average
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        entry,
    )
    conn.commit()
    return entry

def fetch_and_cache_show(tmdb_id, conn):
    cursor = conn.cursor()
    
    # Fetch show data
    tv_url = f"{BASE_URL}/tv/{tmdb_id}"
    tv_response = requests.get(tv_url, params={"api_key": TMDB_API_KEY})
    tv_response.raise_for_status()
    tv_data = tv_response.json()
    
    # Insert show into media table
    show_entry = (
        tv_data["id"],
        tv_data.get("name"),
        "tv",
        IMG_BASE_URL + tv_data["poster_path"] if tv_data.get("poster_path") else None,
        tv_data.get("overview"),
        tv_data.get("first_air_date"),
        None,  # runtime not always available for shows
        tv_data.get("vote_average"),
    )
    
    cursor.execute(
        """
        INSERT OR IGNORE INTO media (
            tmdb_id, title, media_type, poster_url,
            overview, release_date, runtime, vote_average
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        show_entry,
    )
    
    # Insert seasons and their episodes
    for season in tv_data.get("seasons", []):
        season_number = season.get("season_number")
        season_id = f"{tmdb_id}-{season_number}"
        
        # Insert season - adjust column names based on your actual schema
        cursor.execute(
            """
            INSERT OR IGNORE INTO seasons (
                season_id, tv_id, title, season_number,
                name, overview, poster_url, air_date,
                episode_count, vote_average
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                season_id,
                tmdb_id,
                tv_data.get("name"),
                season.get("season_number"),
                season.get("name"),
                season.get("overview"),
                IMG_BASE_URL + season["poster_path"] if season.get("poster_path") else None,
                season.get("air_date"),
                season.get("episode_count"),
                season.get("vote_average"),
            ),
        )
        
        # Fetch and insert episodes for this season
        episode_url = f"{BASE_URL}/tv/{tmdb_id}/season/{season_number}"
        episode_response = requests.get(episode_url, params={"api_key": TMDB_API_KEY})
        if episode_response.ok:
            episodes = episode_response.json().get("episodes", [])
            for ep in episodes:
                # Insert episode - adjust column names based on your actual schema
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO episodes (
                        episode_id, season_id, tv_id, season_number,
                        episode_number, episode_name, overview, air_date,
                        runtime, vote_average, still_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ep["id"],
                        season_id,
                        tmdb_id,
                        season_number,
                        ep.get("episode_number"),
                        ep.get("name"),
                        ep.get("overview"),
                        ep.get("air_date"),
                        ep.get("runtime"),
                        ep.get("vote_average"),
                        IMG_BASE_URL + ep["still_path"] if ep.get("still_path") else None,
                    ),
                )
    
    conn.commit()
    return show_entry