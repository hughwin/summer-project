import requests
import os
import threading
import time
import settings
import html_stripper
import urllib.request
import subprocess
import shutil
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


class UserNotification:
    def __init__(self, status_id, content):
        self.status_id = status_id
        self.content = content
        self.media = []

    def get_status_id(self):
        return self.status_id

    def get_user_content(self):
        return self.get_user_content()

    def get_media(self):
        return self.media

    def add_media(self, media_path):
        self.media.append(media_path)


def listen_to_request():
    count = 0
    status_notifications = []
    while True:
        print("Checking notifications!")
        notifications = mastodon.notifications(mentions_only=True)
        for n in notifications:
            if n["type"] == "mention":
                status_id = n["status"]["id"]
                content = n["status"]["content"]
                user = UserNotification(status_id, content)
                media = n["status"]["media_attachments"]
                for m in media:
                    media_url = m["url"]
                    media_path = "{}.jpg".format(count)
                    urllib.request.urlretrieve(media_url, (str(input_folder / media_path)))
                    user.add_media(count)
                    count += 1
                status_notifications.append(user)
        count = 0
        num_files = os.listdir(str(input_folder))
        if len(num_files) != 0:
            try:
                subprocess.call("python pix2pix/pix2pix.py "
                                "--mode test "
                                "--input_dir pix2pix/val "
                                "--output_dir pix2pix/test "
                                "--checkpoint pix2pix/checkpoint")
            except subprocess.CalledProcessError as e:
                print("Problem with subprocess / pix2pix")
                print(e.output)
        # content = strip_tags(content)  # Removes HTML
        # content = content.replace("@hughwin ", "")
        # params = content.split(" ")
        for reply in status_notifications:
            for image in range(len(reply.get_media())):
                try:
                    image_path = str(output_folder / "{}-outputs.png".format(image))
                    toot_image_on_request(image_path, reply.get_status_id())
                    print("Tooting!")
                except ValueError:
                    print("Something went wrong!")
        mastodon.notifications_clear()
        status_notifications.clear()
        bot_delete_files_in_directory(input_folder)
        bot_delete_files_in_directory(output_folder)
        time.sleep(2)


def bot_delete_files_in_directory(path):
    path = str(path)
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


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
