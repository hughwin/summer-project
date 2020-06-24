import requests
import os
import settings
from mastodon import Mastodon
from dotenv import load_dotenv

# Important variables such as my secret key are stored in a .env file.
# These are loaded as required.
MASTODON_SERVER = settings.BASE_ADDRESS
JSON_ERROR_MESSAGE = "Decoding JSON has failed"
load_dotenv()

#   Set up Mastodon
mastodon = Mastodon(
    access_token=os.getenv("ACCESS_TOKEN"),
    api_base_url=MASTODON_SERVER
)


def get_posts():
    r = requests.get("%sapi/v1/timelines/public?limit=5" % MASTODON_SERVER)  # Consider changing
    statuses = r.json()
    print(statuses[0])
    print(statuses[1])


def post_hello_world():
    mastodon.status_post("Hello world!")


def get_trends():
    try:
        r = requests.get("%s/api/v1/trends/" % MASTODON_SERVER)
        trends = r.json()
        print(trends)
    except ValueError:
        print(JSON_ERROR_MESSAGE)


def get_instance_activity():
    try:
        r = requests.get("%sapi/v1/instance/activity" % MASTODON_SERVER)
        activity = r.json()
        print(activity)
    except ValueError:
        print(JSON_ERROR_MESSAGE)
