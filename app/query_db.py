import pandas as pd
import sqlite3
import os

# load the generated csvs
media_catalog_path = os.path.join(os.path.dirname(__file__), '..', 'media_catalog.csv')
media_df = pd.read_csv(media_catalog_path)

tv_seasons_path = os.path.join(os.path.dirname(__file__), '..', 'tv_seasons.csv')
seasons_df = pd.read_csv(tv_seasons_path)

tv_episodes_path = os.path.join(os.path.dirname(__file__), '..', 'tv_episodes.csv')
episodes_df = pd.read_csv(tv_episodes_path)

conn = sqlite3.connect("media.db")

media_df.to_sql("media", conn, if_exists="replace", index=False)
seasons_df.to_sql("seasons", conn, if_exists="replace", index=False)
episodes_df.to_sql("episodes", conn, if_exists="replace", index=False)

# example query
query = """
SELECT title, runtime
FROM media
WHERE media_type = 'movie' AND runtime IS NOT NULL
ORDER BY runtime DESC;
"""
long_movies = pd.read_sql(query, conn)
print("\nTop movies by runtime:")
print(long_movies.head(10))

conn.close()