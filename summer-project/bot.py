import requests
import os
import threading
import time
import settings
import html_stripper
import urllib.request
from mastodon import Mastodon
from dotenv import load_dotenv
from pathlib import Path, PureWindowsPath

MASTODON_SERVER = settings.BASE_ADDRESS
JSON_ERROR_MESSAGE = "Decoding JSON has failed"
load_dotenv()  # Important variables such as my secret key are stored in a .env file.

#   Set up Mastodon
mastodon = Mastodon(
    access_token=os.getenv("ACCESS_TOKEN"),
    api_base_url=MASTODON_SERVER
)

count = 0
folder = Path("pix2pix/val/")


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


# def toot_image():
#     # image = space_invader_generator.generate_image(3, 16, 64)
#     image_dict = mastodon.media_post(image, mime_type="image/png")
#     mastodon.status_post(status="Fig. " + count, media_ids=image_dict["id"])


def toot_image_on_request(image, post_id):
    image_dict = mastodon.media_post(image, mime_type="image/png")
    message = "Here is my best guess!"
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
        win_folder = PureWindowsPath(folder)
        print(win_folder)
        for n in notifications:
            if n["type"] == "mention":
                status_id = n["status"]["id"]
                content = n["status"]["content"]
                media = n["status"]["media_attachments"][0]["url"]  # Will have to go down another layer
                print(media)
                urllib.request.urlretrieve(media, (str(win_folder / "1.jpg")))
                print("Saving image!")
                content = strip_tags(content)  # Removes HTML
                content = content.replace("@hughwin ", "")
                params = content.split(" ")
                try:
                    size = int(params[0])
                    invaders = int(params[1])
                    # toot_image_on_request(image, status_id)
                    print("Tooting!")
                except ValueError:
                    print("Something went wrong!")
        mastodon.notifications_clear()
        time.sleep(2)


def get_instance_activity():
    try:
        r = requests.get("%sapi/v1/instance/activity" % MASTODON_SERVER)
        activity = r.json()
        # line_graph.plot_weekly_statuses(activity)
    except ValueError:
        print(JSON_ERROR_MESSAGE)


def clear_notifications():
    mastodon.notifications_clear()


def strip_tags(html):
    s = html_stripper.MLStripper()
    s.feed(html)
    return s.get_data()
