import datetime
import os
import shutil
import subprocess
import threading
import time
import numpy
import urllib.request
import pytesseract
import html_stripper
import requests
import schedule
import settings
import cv2
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from mastodon import Mastodon

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
    spam_defender = SpamDefender()
    spam_defender.start()

    listener = threading.Thread(target=listen_to_request(spam_defender))
    listener.start()


def get_posts():
    r = requests.get("%sapi/v1/timelines/public?limit=5" % MASTODON_SERVER)  # Consider changing
    statuses = r.json()
    print(statuses[0])
    print(statuses[1])


def post_error(post_id):
    mastodon.status_post("You're making too many requests!", in_reply_to_id=post_id)


def toot_image_on_request(image_path, post_id):
    image_dict = mastodon.media_post(image_path)
    print(image_dict)
    message = "Here is my best guess!"
    mastodon.status_post(status=message, media_ids=image_dict["id"], in_reply_to_id=post_id)


def toot_image_of_the_day():
    image_of_the_day_path = Path("temp/")
    r = requests.get(settings.NASA_ADDRESS_IMAGES % os.getenv("NASA"))
    json = r.json()
    urllib.request.urlretrieve(json["hdurl"], str(image_of_the_day_path / "image.jpg"))
    image_dict = mastodon.media_post(str(image_of_the_day_path / "image.jpg"))
    message = "Here is today's image!"
    mastodon.status_post(status=message, media_ids=image_dict["id"])
    print("Tooting image of the day!f")


def get_trends():
    try:
        r = requests.get("%s/api/v1/trends/" % MASTODON_SERVER)
        trends = r.json()
        print(trends)
    except ValueError:
        print(JSON_ERROR_MESSAGE)


class UserNotification:
    def __init__(self, account_id, status_id, content):
        self.account_id = account_id
        self.status_id = status_id
        self.content = content
        self.media = []

    def get_account_id(self):
        return self.get_account_id()

    def get_status_id(self):
        return self.status_id

    def get_user_content(self):
        return self.get_user_content()

    def get_media(self):
        return self.media

    def add_media(self, media_path):
        self.media.append(media_path)


class SpamDefender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.users_who_have_made_requests = {}
        self.last_updated_time = datetime.datetime.now()

    def run(self):
        while True:
            now_time = datetime.datetime.now()
            if self.last_updated_time.hour < now_time.hour or self.last_updated_time.day < now_time.day \
                    or self.last_updated_time.month < now_time.month or self.last_updated_time.year < now_time.year:
                self.users_who_have_made_requests.clear()
                self.last_updated_time = now_time
            time.sleep(1)

    def add_user_to_requests(self, account_id):
        if account_id in self.users_who_have_made_requests:
            self.users_who_have_made_requests[account_id] += 1
        else:
            self.users_who_have_made_requests[account_id] = 1

    def allow_account_to_make_request(self, account_id):
        if account_id not in self.users_who_have_made_requests:
            return True
        if self.users_who_have_made_requests[account_id] >= 4:
            return False
        else:
            return True


def listen_to_request(spam_defender):
    count = 0
    status_notifications = []
    schedule.every().day.at("10:30").do(toot_image_of_the_day)
    while True:
        print("Checking notifications!")
        notifications = mastodon.notifications(mentions_only=True)
        for n in notifications:
            if n["type"] == "mention":
                account_id = n["account"]["id"]
                status_id = n["status"]["id"]
                content = n["status"]["content"]
                content = strip_tags(content).replace("@hughwin ", "")
                params = content.split(" ")
                user = UserNotification(account_id, status_id, content)
                media = n["status"]["media_attachments"]
                if not spam_defender.allow_account_to_make_request(account_id):
                    post_error(status_id)
                    print("Denied!")
                else:
                    for m in media:
                        media_url = m["url"]
                        media_path = "{}".format(count)
                        urllib.request.urlretrieve(media_url, (str(input_folder / media_path)))
                        check_image_type(str(input_folder / media_path))
                        user.add_media(count)
                        count += 1
                    status_notifications.append(user)
                    spam_defender.add_user_to_requests(user.account_id)
                count = 0
                num_files = os.listdir(str(input_folder))
                if len(num_files) != 0:
                    print(params)
                    if 'decolourise' in params or 'decolorize' in params:
                        decolourise_image(status_notifications)
                    if "pix2pix" in params:
                        convert_image_using_pix2pix(status_notifications)
                    if "text" in params:
                        get_text_from_image(status_notifications)
            mastodon.notifications_clear()
            status_notifications.clear()
            # bot_delete_files_in_directory(input_folder)
            # bot_delete_files_in_directory(output_folder)
        schedule.run_pending()
        time.sleep(2)


def convert_image_using_pix2pix(status_notifications):
    # TODO: Make this change the files so the right sized images are output.
    try:
        subprocess.call("python pix2pix/pix2pix.py "
                        "--mode test "
                        "--input_dir pix2pix/val "
                        "--output_dir pix2pix/test "
                        "--checkpoint pix2pix/checkpoint")
    except subprocess.CalledProcessError as e:
        print("Problem with subprocess / pix2pix")
        print(e.output)

    for reply in status_notifications:
        for image in range(len(reply.get_media())):
            try:
                image_path = str(output_folder / "{}-outputs.png".format(image))
                toot_image_on_request(image_path, reply.get_status_id())
                print("Tooting!")
            except ValueError as e:
                print("Something went wrong!")
                print(e.output)


def decolourise_image(status_notifications):
    for reply in status_notifications:
        for image in range(len(reply.get_media())):
            image_path = str(input_folder / "{}".format(image))
            img_open = cv2.imread(image_path)
            gray = cv2.cvtColor(img_open, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(str(output_folder / "{}.jpeg".format(image)), gray)
            toot_image_on_request(image_path, reply.get_status_id())


def get_text_from_image(status_notifications):
    for reply in status_notifications:
        for image in range(len(reply.get_media())):

            pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract'
            # Must be local install path of tesseract
            img = cv2.imread(str(input_folder / "{}".format(image)))
            file = open("recognized.txt", "a")
            text = pytesseract.image_to_string(img)


def check_image_type(filepath):
    filepath_with_jpg = str(filepath + ".jpg")
    if not is_jpg(filepath):
        im = Image.open(filepath)
        rgb_image = im.convert('RGB')
        rgb_image.save(filepath_with_jpg)
    else:
        os.renames(str(filepath), filepath_with_jpg)


def combine_image(filepath1, filepath2=None):
    if filepath2 is None:
        filepath2 = filepath1
    img1 = Image.open(filepath1)
    img2 = Image.open(filepath2)
    images = [img1, img2]
    combined_image = append_images(images, direction="horizontal")
    combined_image.save(filepath1)


def is_jpg(filepath):
    data = open(filepath, 'rb').read(11)
    if data[:4] != '\xff\xd8\xff\xe0': return False
    if data[6:] != 'JFIF\0': return False
    return True


def append_images(images, direction='horizontal',
                  bg_color=(255, 255, 255), aligment='center'):
    widths, heights = zip(*(i.size for i in images))

    if direction == 'horizontal':
        new_width = sum(widths)
        new_height = max(heights)
    else:
        new_width = max(widths)
        new_height = sum(heights)

    new_im = Image.new('RGB', (new_width, new_height), color=bg_color)

    offset = 0
    for im in images:
        if direction == 'horizontal':
            y = 0
            if aligment == 'center':
                y = int((new_height - im.size[1]) / 2)
            elif aligment == 'bottom':
                y = new_height - im.size[1]
            new_im.paste(im, (offset, y))
            offset += im.size[0]
        else:
            x = 0
            if aligment == 'center':
                x = int((new_width - im.size[0]) / 2)
            elif aligment == 'right':
                x = new_width - im.size[0]
            new_im.paste(im, (x, offset))
            offset += im.size[1]

    return new_im


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
