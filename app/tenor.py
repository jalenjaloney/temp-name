import requests
import os
from dotenv import load_dotenv

# set the apikey
load_dotenv()
tenor_key = os.getenv("TENOR_API_KEY")

def search_gif(query, limit=20, pos=None):
    if not query:
        return []
   
    url = "https://tenor.googleapis.com/v2/search"
    params = {
        "q": query,
        "key": tenor_key,
        "limit": limit,
        # 'pos' is pagination token that specifies where to continue the search
        "pos": str(pos)
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        gifs = []
        # Extract the .gif URL from each result
        for result in data["results"]:
            url = result["media_formats"]["gif"]["url"]
            gifs.append(url)
        # Save the position for the next request to start from
        next_pos = data.get("next", None)
        return {"gifs": gifs, "next": next_pos}
    else:
        # If API call fails, return an empty list
        return {"gifs": [], "next": None}

def featured_gifs(limit=20):
    url = "https://tenor.googleapis.com/v2/featured"
    params = {
        "key": tenor_key,
        "limit": limit
    }

    response = requests.get(url, params)
    if response.status_code == 200:
        data = response.json()
        links = []
        # Extract the .gif URL from each result
        for result in data["results"]:
            url = result["media_formats"]["gif"]["url"]
            links.append(url)
        return links
    else:
        # If API call fails, return an empty list
        return []
