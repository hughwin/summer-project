import requests
import os
import threading
import time
import settings
import line_graph
import html_stripper
import space_invader_generator
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


def start_bot():
    x = threading.Thread(target=listen_to_request_for_invader())
    x.start()


def get_posts():
    r = requests.get("%sapi/v1/timelines/public?limit=5" % MASTODON_SERVER)  # Consider changing
    statuses = r.json()
    print(statuses[0])
    print(statuses[1])


def post_hello_world():
    mastodon.status_post("Hello world!")
    # TODO: Consider removing this method.


def toot_image():
    image = space_invader_generator.generate_image(3, 16, 64)
    image_dict = mastodon.media_post(image, mime_type="image/png")
    mastodon.status_post(status="A space invader", media_ids=image_dict["id"])


def toot_image_on_request(image, post_id):
    image_dict = mastodon.media_post(image, mime_type="image/png")
    message = "Here is your bespoke space invader!"
    mastodon.status_post(status=message, media_ids=image_dict["id"], in_reply_to_id=post_id)


def get_trends():
    try:
        r = requests.get("%s/api/v1/trends/" % MASTODON_SERVER)
        trends = r.json()
        print(trends)
    except ValueError:
        print(JSON_ERROR_MESSAGE)


def listen_to_request_for_invader():
    while True:
        print("Checking notifications!")
        notifications = mastodon.notifications(mentions_only=True)
        for n in notifications:
            if n["type"] == "mention":
                status_id = n["status"]["id"]
                content = n["status"]["content"]
                media = n["status"]["media_attachments"]
                print(n)
                print(media)
                content = strip_tags(content)  # Removes HTML
                content = content.replace("@hughwin ", "")
                params = content.split(" ")
                try:
                    size = int(params[0])
                    invaders = int(params[1])
                    image = space_invader_generator.generate_image(size, invaders, (size * invaders + 1))
                    toot_image_on_request(image, status_id)
                    print("Tooting!")
                except ValueError:
                    print("Something went wrong!")
        mastodon.notifications_clear()
        time.sleep(2)


def get_instance_activity():
    try:
        r = requests.get("%sapi/v1/instance/activity" % MASTODON_SERVER)
        activity = r.json()
        line_graph.plot_weekly_statuses(activity)
    except ValueError:
        print(JSON_ERROR_MESSAGE)


def clear_notifications():
    mastodon.notifications_clear()


def strip_tags(html):
    s = html_stripper.MLStripper()
    s.feed(html)
    return s.get_data()
