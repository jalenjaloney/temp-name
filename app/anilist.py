import requests
import pandas as pd
# import os
# from dotenv import load_dotenv
# anilist api uses oauth, don't need token for public data

# All GraphQL requests made as POST requests to this url (API endpoint)
ANILIST_URL = "https://graphql.anilist.co"
# GraphQL query to fetch trending anime w/ relevant fields
QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(type: ANIME, sort: TRENDING_DESC) {
      id
      title {
        romaji
        english
      }
      episodes
      duration
      averageScore
      trending
      genres
      description(asHtml: false)
      coverImage {
        large
      }
      startDate {
        year
        month
        day
      }
    }
  }
}
"""
# get anime info from api
def fetch_anime(pages):
    all_anime = []
    for page in range(1, pages + 1):
        response = requests.post(
            ANILIST_URL,
            json={"query": QUERY, "variables": {"page": page, "perPage": 25}},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        all_anime.extend(data["data"]["Page"]["media"])
    return all_anime

# if there are missing parts of date
def format_start_date(start_date):
    year = start_date.get("year")
    month = start_date.get("month")
    day = start_date.get("day")
    if not year:
        return ""
    if month and day:
        return f"{month:02d}-{day:02d}-{year}"
    elif month:
        return f"{month:02d}-{year}"
    else:
        return str(year)
# extract necessary fields from TV show seasons data
def parse_anime(anime_raw):
    parsed = []
    for anime in anime_raw:
        parsed.append({
            "anilist_id": anime["id"],
            "title_romaji": anime["title"]["romaji"],
            "title_english": anime["title"]["english"],
            "episodes": anime["episodes"],
            "duration": anime["duration"],
            "average_score": anime["averageScore"],
            "genres": ", ".join(anime["genres"]),
            "description": anime["description"],
            "cover_url": anime["coverImage"]["large"],
            "start_date": format_start_date(anime["startDate"]),
        })
    return parsed

# currentlly fetches 100 entires/animes; currently running into rate limit issues
anime_raw = fetch_anime(pages=4)
anime_data = parse_anime(anime_raw)
pd.DataFrame(anime_data).to_csv("anime_catalog.csv", index=False)
print("Saved anime_catalog.csv with", len(anime_data), "entries")