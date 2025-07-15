import pandas as pd
import sqlite3

# load the generated csvs
media_df = pd.read_csv("media_catalog.csv")
seasons_df = pd.read_csv("tv_seasons.csv")
episodes_df = pd.read_csv("tv_episodes.csv")

conn = sqlite3.connect("media.db")

media_df.to_sql("media", conn, if_exists="replace", index=False)
seasons_df.to_sql("seasons", conn, if_exists="replace", index=False)
episodes_df.to_sql("episodes", conn, if_exists="replace", index=False)

# example query
query = """
SELECT title, COUNT(*) AS season_count
FROM seasons
GROUP BY title
ORDER BY season_count DESC;
"""
season_counts = pd.read_sql(query, conn)
print("\nTop shows by number of seasons:")
print(season_counts.head(10))

conn.close()