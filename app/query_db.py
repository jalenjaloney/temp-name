import pandas as pd
import sqlite3
import os

# loads csvs, populates database w/ media, episodes, seasons
def create_media_db(db_path="media.db"):
    base_dir = os.path.dirname(__file__)
    # media related csvs
    media_catalog_path = os.path.join(base_dir, "..", "media_catalog.csv")
    tv_seasons_path = os.path.join(base_dir, "..", "tv_seasons.csv")
    tv_episodes_path = os.path.join(base_dir, "..", "tv_episodes.csv")

    # Load media CSVs
    media_df = pd.read_csv(media_catalog_path)
    seasons_df = pd.read_csv(tv_seasons_path)
    episodes_df = pd.read_csv(tv_episodes_path)
    
    # anime related csvs
    anime_catalog_path = os.path.join(base_dir, "..", "anime_catalog.csv")
    anime_episodes_path = os.path.join(base_dir, "..", "anime_episodes.csv")

    # load anime csvs
    anime_df = pd.read_csv(anime_catalog_path)
    anime_eps_df = pd.read_csv(anime_episodes_path)

    # Fill missing runtime if needed
    if "runtime" not in media_df.columns:
        media_df["runtime"] = 60  # fallback
    else:
        media_df["runtime"] = media_df["runtime"].fillna(60)
    if "duration" not in anime_df.columns:
        anime_df["duration"] = 60
    else:
        anime_df["duration"] = anime_df["duration"].fillna(60)


    # Write to SQLite
    conn = sqlite3.connect(db_path)
    # media
    media_df.to_sql("media", conn, if_exists="replace", index=False)
    seasons_df.to_sql("seasons", conn, if_exists="replace", index=False)
    episodes_df.to_sql("episodes", conn, if_exists="replace", index=False)

    # anime data
    anime_df.to_sql("anime", conn, if_exists="replace", index=False)
    anime_eps_df.to_sql("anime_ep", conn, if_exists="replace", index=False)

    conn.close()


if __name__ == "__main__":
    create_media_db()