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
import imutils
from matplotlib import pyplot as plt
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv
from mastodon import Mastodon

MASTODON_SERVER = settings.BASE_ADDRESS
JSON_ERROR_MESSAGE = "Decoding JSON has failed"
INPUT_FOLDER = settings.INPUT_FOLDER
OUTPUT_FOLDER = settings.OUTPUT_FOLDER
JPEG_INPUT = settings.JPEG_INPUT
JPEG_OUTPUT = settings.JPEG_INPUT
load_dotenv()  # Important variables such as my secret key are stored in a .env file.

#   Set up Mastodon
mastodon = Mastodon(
    access_token=os.getenv("ACCESS_TOKEN"),
    api_base_url=MASTODON_SERVER
)


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


def reply_to_toot(post_id, image_path=None, message=None, meta=None):
    if image_path is None:
        mastodon.status_post(status=message, in_reply_to_id=post_id)
    else:
        image_dict = mastodon.media_post(image_path)
        if meta is not None:
            image_dict["meta"] == meta
        mastodon.status_post(status=message, media_ids=image_dict["id"], in_reply_to_id=post_id)


def toot_image_of_the_day():
    image_of_the_day_path = Path("temp/")
    r = requests.get(settings.NASA_ADDRESS_IMAGES % os.getenv("NASA"))
    json = r.json()
    urllib.request.urlretrieve(json["hdurl"], str(image_of_the_day_path / "image.jpeg"))
    image_dict = mastodon.media_post(str(image_of_the_day_path / "image.jpeg"))
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
        self.meta = []


class SpamDefender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.users_who_have_made_requests = {}
        self.last_updated_time = datetime.datetime.now()

    def __setattr__(self, key, value):
        raise Exception("Can't change attributes directly!")

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


# TODO: Just change image dictionary.

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
                content = strip_tags(content).replace("@hughwin ", "").lower()
                params = content.split(" ")
                user = UserNotification(account_id, status_id, content)
                media = n["status"]["media_attachments"]
                if not spam_defender.allow_account_to_make_request(account_id):
                    reply_to_toot(status_id, message="You're making too many requests!")
                    print("Denied!")
                else:
                    for m in media:
                        if m["type"] == "image":
                            media_url = m["url"]
                            media_path = "{}".format(count)
                            urllib.request.urlretrieve(media_url, (str(INPUT_FOLDER / media_path)))
                            check_image_type(str(INPUT_FOLDER / media_path))
                            user.media = count
                            user.meta = ["meta"]
                            count += 1
                    status_notifications.append(user)
                    spam_defender.add_user_to_requests(user.account_id)
                count = 0
                num_files = os.listdir(str(INPUT_FOLDER))
                if len(num_files) != 0:
                    print(params)
                    if 'decolourise' in params or 'decolorize' in params:
                        decolourise_image(status_notifications)
                    if "pix2pix" in params:
                        convert_image_using_pix2pix(status_notifications)
                    if "text" in params:
                        get_text_from_image(status_notifications)
                    if "about" in params:
                        get_information_about_image(status_notifications)
                    if "preserve" in params:
                        display_colour_channel(status_notifications, params[params.index("preserve") + 1])
                    if "histogram" in params:
                        show_image_histogram(status_notifications)
                    if settings.ROTATE_COMMAND in params:
                        rotate_image(status_notifications,
                                     rotate_by_degrees=params[params.index(settings.ROTATE_COMMAND) + 1],
                                     rotation_type=params[params.index(settings.ROTATE_COMMAND) + 2])
            mastodon.notifications_clear()
            status_notifications.clear()
            # bot_delete_files_in_directory(INPUT_FOLDER)
            # bot_delete_files_in_directory(OUTPUT_FOLDER)
        schedule.run_pending()
        time.sleep(2)


def get_information_about_image(status_notifications):
    for reply in status_notifications:
        for image in range(len(reply.media)):
            input_image = JPEG_INPUT.format(image)
            img_open = cv2.imread(input_image)
            message = "Image properties: " \
                      "\n- Number of Pixels: " + str(img_open.size) \
                      + "\n- Shape/Dimensions: " + str(img_open.shape)
            reply_to_toot(reply.status_id, message=message)


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
        for image in range(len(reply.media)):
            try:
                image_path = str(OUTPUT_FOLDER / "{}-outputs.png".format(image))
                reply_to_toot(reply.status_id, image_path=image_path)
                print("Tooting!")
            except ValueError as e:
                print("Something went wrong!")
                print(e.output)


def decolourise_image(status_notifications):
    for reply in status_notifications:
        for image in range(len(reply.media)):
            input_image = JPEG_INPUT.format(image)
            output_image = JPEG_OUTPUT.format(image)
            img_open = cv2.imread(input_image)
            gray = cv2.cvtColor(img_open, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(output_image, gray)
            reply_to_toot(reply.status_id, image_path=output_image, meta=reply.meta)


def display_colour_channel(status_notifications, colour):
    colour = colour()
    for reply in status_notifications:
        for image in range(len(reply.media)):
            image_open = cv2.imread(JPEG_INPUT.format(image))
            temp_image = image_open.copy()
            if colour == "red":
                temp_image[:, :, 0] = 0
                temp_image[:, :, 1] = 0
            if colour == "green":
                temp_image[:, :, 0] = 0
                temp_image[:, :, 2] = 0
            if colour == "blue":
                temp_image[:, :, 1] = 0
                temp_image[:, :, 2] = 0
            cv2.imwrite(JPEG_OUTPUT.format(image), temp_image)
            reply_to_toot(reply.status_id, image_path=JPEG_OUTPUT.format(image), meta=reply.meta)


def get_text_from_image(status_notifications):
    for reply in status_notifications:
        for image in range(len(reply.media)):
        # TODO:
            pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract'
            # Must be local install path of tesseract
            img = cv2.imread(JPEG_INPUT.format(image))
            text = pytesseract.image_to_string(img)

            if len(text) <= settings.MAX_MESSAGE_LENGTH:
                reply_to_toot(reply.status_id, message=text)
            else:
                parts = []
                while len(text) > 0:
                    if len(text) > settings.MAX_MESSAGE_LENGTH:
                        parts.append(part)
                        print(part)
                        text = text[settings.MAX_MESSAGE_LENGTH:]
                    else:
                        parts.append(text)
                        break

                for part in parts:
                    print(part)
                    reply_to_toot(reply.status_id, message=part)
                    time.sleep(1)


def check_image_type(filepath):
    filepath_with_jpeg = str(filepath + ".jpeg")
    if not is_jpg(filepath):
        im = Image.open(filepath)
        rgb_image = im.convert('RGB')
        rgb_image.save(filepath_with_jpeg)
    else:
        os.renames(str(filepath), filepath_with_jpeg)


def rotate_image(status_notifications, rotate_by_degrees=None, rotation_type=None):
    for reply in status_notifications:
        for image in range(len(reply.media)):
            input_image = JPEG_INPUT.format(image)
            output_image = JPEG_OUTPUT.format(image)
            image_open = cv2.imread(input_image)
            if str(rotation_type)() == settings.ROTATE_COMMAND:
                rotated = imutils.rotate(image_open, int(rotate_by_degrees))
            else:
                rotated = imutils.rotate_bound(image_open, int(rotate_by_degrees))
            cv2.imwrite(output_image, rotated)
            reply_to_toot(reply.status_id, image_path=output_image,
                          message=(str("Rotated by {} degrees").format(rotate_by_degrees)), meta=reply.meta)


def combine_image(filepath1, filepath2=None):
    if filepath2 is None:
        filepath2 = filepath1
    img1 = Image.open(filepath1)
    img2 = Image.open(filepath2)
    images = [img1, img2]
    combined_image = append_images(images, direction="horizontal")
    combined_image.save(filepath1)


def show_image_histogram(status_notifications):
    for reply in status_notifications:
        for image in range(len(reply.media)):
            input_image = cv2.imread(JPEG_INPUT.format(image))
            color = ('b', 'g', 'r')
            for i, col in enumerate(color):
                histogram = cv2.calcHist([input_image], [i], None, [256], [0, 256])
                plt.plot(histogram, color=col)
                plt.xlim([0, 256])
            plt.draw()
            plt.savefig(JPEG_OUTPUT.format(image), bbox_inches='tight')
            reply_to_toot(reply.status_id, image_path=JPEG_OUTPUT.format(image),
                          message="Histogram")


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
