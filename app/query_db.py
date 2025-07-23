import pandas as pd
import sqlite3
import os

def create_media_db(db_path="media.db"):
    """
    Loads CSVs and populates an SQLite database with media, seasons, and episodes tables.
    Optionally specify a custom db_path.
    """
    base_dir = os.path.dirname(__file__)
    media_catalog_path = os.path.join(base_dir, "..", "media_catalog.csv")
    tv_seasons_path = os.path.join(base_dir, "..", "tv_seasons.csv")
    tv_episodes_path = os.path.join(base_dir, "..", "tv_episodes.csv")

    # Load CSVs
    media_df = pd.read_csv(media_catalog_path)
    seasons_df = pd.read_csv(tv_seasons_path)
    episodes_df = pd.read_csv(tv_episodes_path)

    # Fill missing runtime if needed
    if "runtime" not in media_df.columns:
        media_df["runtime"] = 60  # fallback
    else:
        media_df["runtime"] = media_df["runtime"].fillna(60)

    # Write to SQLite
    conn = sqlite3.connect(db_path)
    media_df.to_sql("media", conn, if_exists="replace", index=False)
    seasons_df.to_sql("seasons", conn, if_exists="replace", index=False)
    episodes_df.to_sql("episodes", conn, if_exists="replace", index=False)

    conn.close()
create_media_db()