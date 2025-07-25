import requests
import pandas as pd
import time # rate limits
import re
import html
# import os
# from dotenv import load_dotenv
# anilist api uses oauth, don't need token for public data

# All GraphQL requests made as POST requests to this url (API endpoint)
ANILIST_URL = "https://graphql.anilist.co"
# GraphQL query to fetch trending anime w/ relevant fields
MAIN_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(type: ANIME, sort: TRENDING_DESC) {
      id
      title {
        romaji
        english
      }
      episodes
      
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

# query for anime episodes/seasons
EPISODE_QUERY = """
query ($id: Int) {
  Media(id: $id, type: ANIME) {
    id
    duration
    streamingEpisodes {
      title
      thumbnail
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
            json={"query": MAIN_QUERY, "variables": {"page": page, "perPage": 15}},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        # add to all_anime list
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
    
# extract necessary fields from anime data
def parse_anime(anime_raw):
    parsed = []
    for anime in anime_raw:
        # clean up the desciptions before appending
        raw_description = anime["description"]

        cleaned_descrip = raw_description

        # remove the HTML tags and decode the entries
        cleaned_descrip = re.sub(r'<[^>]*>', '', cleaned_descrip)
        cleaned_descrip = html.unescape(cleaned_descrip)

        cleaned_descrip = re.sub(r'\(Source:.*', '', cleaned_descrip, flags=re.DOTALL)
        cleaned_descrip = re.sub(r'Notes:.*', '', cleaned_descrip, flags=re.IGNORECASE | re.DOTALL)

        # remove tags
        cleaned_descrip = cleaned_descrip.replace('<br>', '\n')
        cleaned_descrip = re.sub(r'\n+', '\n', cleaned_descrip)
        cleaned_descrip = cleaned_descrip.strip()


        parsed.append({
            "anilist_id": anime["id"],
            "title_romaji": anime["title"]["romaji"],
            "title_english": anime["title"]["english"],
            "episodes": anime["episodes"],
            #"duration": anime["duration"],
            "average_score": f"{anime['averageScore'] / 10:.1f}" if anime["averageScore"] is not None else None,
            "trending": anime["trending"],
            "genres": ", ".join(anime["genres"]),
            "description": cleaned_descrip,
            "cover_url": anime["coverImage"]["large"],
            "start_date": format_start_date(anime["startDate"]),
        })
    return parsed

# currently fetches 15 entries/animes; running into rate limit issues with more pages, saves into csv
anime_raw = fetch_anime(pages=1)
anime_data = parse_anime(anime_raw)
pd.DataFrame(anime_data).to_csv("anime_catalog.csv", index=False)
print("Saved anime_catalog.csv with", len(anime_data), "entries")

# get episode info from anime from api
def fetch_episodes(anilist_id):
    response = requests.post(
        ANILIST_URL,
        json={
            "query": EPISODE_QUERY,
            "variables": {"id": anilist_id}
        },
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    data = response.json()
    media = data.get("data", {}).get("Media", {})

    return {
        "streamingEpisodes": media.get("streamingEpisodes", []),
        "duration": media.get("duration")
    }

# try to get episode num
def extract_ep_num(episode_title):
    if episode_title:
        # all title starts w/ episode _
        match = re.match(r'^(?:Episode|Ep)?\s*(\d+)', episode_title, re.IGNORECASE)
        if match:
            return int(match.group(1))
        # if no leading num
        num_match = re.match(r'^(\d+)', episode_title)
        if num_match:
            return int(num_match.group(1))
    return 0

# get the title and thumbnail
def parse_episodes(anilist_id, episodes_data):
    parsed = []

    episodes_raw = episodes_data.get("streamingEpisodes", [])
    anime_duration = episodes_data.get("duration")

    # create an episode id
    numbered_eps = []
    for ep in episodes_raw:
        ep_num = extract_ep_num(ep.get("title"))
        numbered_eps.append((ep_num, ep))
    numbered_eps.sort(key=lambda x: x[0])

    for ep_num, episode in numbered_eps:
        custom_episode_id = (anilist_id * 1000) + ep_num

        parsed.append({
            "anilist_id": anilist_id,
            "episode_id": custom_episode_id,
            "episode_title": episode.get("title"),
            "thumbnail": episode.get("thumbnail"),
            "duration": anime_duration,
        })
    return parsed

# Take episode data, store in csvs
def generate_episode_csvs():
    all_episodes = []
    for anime in anime_data:
        try:
            #debug
            # print(f"Fetching episodes for: {anime['title_romaji']}")
            episodes_raw = fetch_episodes(anime["anilist_id"])
            parsed_eps = parse_episodes(anime["anilist_id"], episodes_raw)
            all_episodes.extend(parsed_eps)
            # delay bc of rate limiting
            time.sleep(1.8)
        except Exception as e:
            print(f"failed to fetch episodes for {anime.get('title_english')}: {e}")

    pd.DataFrame(all_episodes).to_csv("anime_episodes.csv", index=False)
    print("Saved anime_episodes.csv with", len(all_episodes), "entries")

if __name__ == "__main__":
    generate_episode_csvs()