import requests
import os
from mastodon import Mastodon
from dotenv import load_dotenv

# Important variables such as my secret key are stored in a .env file.
# These are loaded as required.
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


def get_trends():
    try:
        r = requests.get("https://hostux.social/api/v1/trends/")
        trends = r.json()
        print(trends)
    except ValueError:
        print("Decoding JSON has failed")


def get_instance_activity():
    try:
        r = requests.get("https://hostux.social/api/v1/instance/activity")
        activity = r.json()
        print(activity)
    except ValueError:
        print("Decoding JSON has failed")
