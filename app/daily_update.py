import subprocess

print("Fetching new media data from TMDb...")
subprocess.run(["python3", "app/tmdb.py"])

print("Fetching AniList data...")
subprocess.run(["python3", "app/anilist.py"])

print("Rebuilding SQLite database...")
subprocess.run(["python3", "app/query_db.py"])

print("Media database successfully updated.")