import subprocess

print("Fetching new media data from TMDb...")
subprocess.run(["python3", "app/tmdb.py"])

print("Rebuilding SQLite database...")
subprocess.run(["python3", "app/query_db.py"])

print("Media database successfully updated.")