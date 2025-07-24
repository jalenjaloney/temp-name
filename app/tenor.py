import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
'''
tenor_key = os.getenv("TENOR_API_KEY")

# search for excited top 8 GIFs
url = "https://tenor.googleapis.com/v2/search"
params = {
    "q": "excited",
    "key": tenor_key,
    "limit": 5
}

response = requests.get(url, params)
print(response.json())
'''

# set the apikey
tenor_key = os.getenv("TENOR_API_KEY")  # click to set to your apikey
ckey = "my_test_app"  # set the client_key for the integration
lmt = 10

# get the top 10 featured GIFs - using the default locale of en_US
r = requests.get("https://tenor.googleapis.com/v2/featured?key=%s&client_key=%s&limit=%s" % (tenor_key, ckey, lmt))

if r.status_code == 200:
    featured_gifs = json.loads(r.content)
else:
    featured_gifs = None

# get the current list of categories - using the default locale of en_US
r = requests.get("https://tenor.googleapis.com/v2/categories?key=%s&client_key=%s" % (tenor_key, ckey))

if r.status_code == 200:
    categories = json.loads(r.content)
else:
    categories = None

# load either the featured GIFs or categories below the search bar for the user
# for GIFs use the smaller formats for faster load times
print (featured_gifs)
print (categories)

'''
lmt = 8

# our test search
search_term = "excited"

# get the top 8 GIFs for the search term
r = requests.get(
    "https://tenor.googleapis.com/v2/search?q=%s&key=%s&client_key=%s&limit=%s" % (search_term, tenor_key, ckey,  lmt))

if r.status_code == 200:
    # load the GIFs using the urls for the smaller GIF sizes
    top_8gifs = json.loads(r.content)
    print(top_8gifs)
else:
    top_8gifs = None

# get the GIF's id and search used
shard_gifs_id = top_8gifs["results"][0]["id"]

search_term = "excited"

r = requests.get("https://tenor.googleapis.com/v2/registershare?id=%s&key=%s&client_key=%s&q=%s" % (shard_gifs_id, tenor_key, ckey, search_term))

if r.status_code == 200:
    pass
    # move on
else:
    pass
    # handle error
'''