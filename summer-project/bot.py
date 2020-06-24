import requests
import os
from mastodon import Mastodon
from dotenv import load_dotenv

load_dotenv()


#   Set up Mastodon
mastodon = Mastodon(
    access_token=os.getenv("ACCESS_TOKEN"),
    api_base_url='https://hostux.social/'
)


def get_posts():
    r = requests.get("https://hostux.social/api/v1/timelines/public?limit=5")
    statuses = r.json()
    print(statuses[0])
    print(statuses[1])


def post_hello_world():
    mastodon.status_post("Hello world!")