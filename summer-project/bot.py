import requests
import os
import threading
import time
import settings
import html_stripper
import urllib.request
import subprocess
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

input_folder = Path("pix2pix/val/")
output_folder = Path("pix2pix/test/images/")


def start_bot():
    x = threading.Thread(target=listen_to_request())
    x.start()


def get_posts():
    r = requests.get("%sapi/v1/timelines/public?limit=5" % MASTODON_SERVER)  # Consider changing
    statuses = r.json()
    print(statuses[0])
    print(statuses[1])


def post_hello_world():
    mastodon.status_post("Hello world!")
    # TODO: Consider removing this method.


def toot_image_on_request(image_path, post_id):
    image_dict = mastodon.media_post(image_path)
    print(image_dict)
    message = "Here is my best guess!"
    mastodon.status_post(status=message, media_ids=image_dict["id"], in_reply_to_id=post_id)


def get_trends():
    try:
        r = requests.get("%s/api/v1/trends/" % MASTODON_SERVER)
        trends = r.json()
        print(trends)
    except ValueError:
        print(JSON_ERROR_MESSAGE)


def listen_to_request():
    while True:
        count = 0
        print("Checking notifications!")
        notifications = mastodon.notifications(mentions_only=True)
        for n in notifications:
            if n["type"] == "mention":
                status_id = n["status"]["id"]
                content = n["status"]["content"]
                media = n["status"]["media_attachments"]
                for m in media:
                    media_url = m["url"]
                    urllib.request.urlretrieve(media_url, (str(input_folder / "{}.jpg".format(count))))
                    count += 1
                    try:
                        subprocess.call("python pix2pix/pix2pix.py "
                                        "--mode test "
                                        "--input_dir pix2pix/val "
                                        "--output_dir pix2pix/test "
                                        "--checkpoint pix2pix/checkpoint")
                    except Exception:
                        print("Problem with TensorFlow")
                content = strip_tags(content)  # Removes HTML
                content = content.replace("@hughwin ", "")
                params = content.split(" ")
                output_count = 0
                for i in range(count):
                    try:
                        image_path = str(output_folder / "{}-outputs.png".format(output_count))
                        toot_image_on_request(image_path, status_id)
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
