import requests
import os
import settings
import line_graph
import html_stripper
from mastodon import Mastodon
from dotenv import load_dotenv


MASTODON_SERVER = settings.BASE_ADDRESS
JSON_ERROR_MESSAGE = "Decoding JSON has failed"
load_dotenv()  # Important variables such as my secret key are stored in a .env file.

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
    # TODO: Consider removing this method.


def toot_image(image):
    image_dict = mastodon.media_post(image)
    mastodon.status_post(status="A space invader", media_ids=image_dict["id"])


def toot_image_on_request(image, user_id):
    image_dict = mastodon.media_post(image)
    mastodon.status_post(status="A space invader", media_ids=image_dict["id"])


def get_trends():
    try:
        r = requests.get("%s/api/v1/trends/" % MASTODON_SERVER)
        trends = r.json()
        print(trends)
    except ValueError:
        print(JSON_ERROR_MESSAGE)


def get_mentions():
    notifications = mastodon.notifications(mentions_only=True)
    for n in notifications:
        if n["type"] == "mention":
            content = (n["status"]["content"])
            content = strip_tags(content)
            print(content)
            # message = n["mention"]["content"]
            user_id = n["id"]


def get_instance_activity():
    try:
        r = requests.get("%sapi/v1/instance/activity" % MASTODON_SERVER)
        activity = r.json()
        line_graph.plot_weekly_statuses(activity)
    except ValueError:
        print(JSON_ERROR_MESSAGE)


def strip_tags(html):
    s = html_stripper.MLStripper()
    s.feed(html)
    return s.get_data()
