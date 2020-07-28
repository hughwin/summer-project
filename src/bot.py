import datetime
import os
import shutil
import subprocess
import threading
import time
import urllib.request
import pytesseract
import html_stripper
import requests
import schedule
import settings
import cv2
import imutils
from dotenv import load_dotenv
from matplotlib import pyplot as plt
from pathlib import Path
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from mastodon import Mastodon

load_dotenv()  # Important variables such as my secret key are stored in a .env file.

#   Set up Mastodon
mastodon = Mastodon(
    access_token=os.getenv("ACCESS_TOKEN"),
    api_base_url=settings.BASE_ADDRESS
)

def start_bot():
    spam_defender = SpamDefender()
    spam_defender.start()
    listener = threading.Thread(target=listen_to_request(spam_defender))
    listener.start()


def reply_to_toot(post_id, message=None, meta=None):
    media_ids = []
    for fn in os.listdir(str(settings.INPUT_FOLDER)):
        if fn.endswith(('.jpeg', '.png')):
            print(Path(fn))
            image_dict = mastodon.media_post(str(settings.INPUT_FOLDER / fn))
            media_ids.append(image_dict["id"])

    parts = []
    while len(message) > 0:
        parts.append(message[:settings.MAX_MESSAGE_LENGTH])
        message = message[settings.MAX_MESSAGE_LENGTH:]
    for part in parts:
        print(part)
        mastodon.status_post(status=part, media_ids=media_ids, in_reply_to_id=post_id)


def toot_image_of_the_day():
    r = requests.get(settings.NASA_ADDRESS_IMAGES % os.getenv("NASA"))
    json = r.json()
    print(json)
    urllib.request.urlretrieve(json["hdurl"], settings.DAILY_IMAGE)
    image_dict = mastodon.media_post(settings.DAILY_IMAGE)
    message = "Here is today's image!"
    mastodon.status_post(status=message, media_ids=image_dict["id"])
    print("Tooting image of the day!")
    bot_delete_files_in_directory(settings.DAILY_IMAGE)


def get_trends():
    try:
        r = requests.get("%s/api/v1/trends/" % settings.BASE_ADDRESS)
        trends = r.json()
        print(trends)
    except ValueError:
        print(settings.JSON_ERROR_MESSAGE)


class UserNotification:
    def __init__(self, account_id, status_id, content, params):
        self.account_id = account_id
        self.status_id = status_id
        self.content = content
        self.params = params
        self.media = []
        self.meta = []


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
                print(params)
                user = UserNotification(account_id, status_id, content, params)
                media = n["status"]["media_attachments"]
                if "help" in params:
                    print("help")
                    reply_to_toot(status_id, message=settings.HELP_MESSAGE)
                if not spam_defender.allow_account_to_make_request(account_id):
                    reply_to_toot(status_id, message=settings.TOO_MANY_REQUESTS_MESSAGE)
                    print("Denied!")
                else:
                    for m in media:
                        if m["type"] == "image":
                            media_url = m["url"]
                            media_path = "{}".format(count)
                            urllib.request.urlretrieve(media_url, (str(settings.INPUT_FOLDER / media_path)))
                            check_image_type(str(settings.INPUT_FOLDER / media_path))
                            user.media.append(media)
                            user.meta = ["meta"]
                            count += 1
                    status_notifications.append(user)
                    spam_defender.add_user_to_requests(user.account_id)
                count = 0
                num_files = os.listdir(str(settings.INPUT_FOLDER))
                if len(num_files) != 0:
                    for reply in status_notifications:
                        print(reply.params)
                        if 'decolourise' in reply.params or 'decolorize' in params:
                            decolourise_image(reply)
                        if "text" in params:
                            get_text_from_image(reply)
                        if "about" in params:
                            get_information_about_image(reply)
                        if "preserve" in params:
                            display_colour_channel(reply, params[params.index("preserve") + 1])
                        if "histogram" in params:
                            show_image_histogram(reply)
                        if "border" in params:
                            create_border(reply)
                        if "crop" in params:
                            crop_image(reply)
                        if "enhance" in params:
                            enhance_image(reply)
                        if "brightness" in params:
                            try:
                                adjust_brightness(reply, value=params[params.index("brightness") + 1])
                            except IndexError:
                                adjust_brightness(reply)
                        if "contrast" in params:
                            try:
                                adjust_contrast(reply, value=params[params.index("contrast") + 1])
                            except IndexError:
                                adjust_contrast(reply)
                        if "colour" in params:
                            try:
                                adjust_colour(reply, value=params[params.index("colour") + 1])
                            except IndexError:
                                adjust_contrast(reply)
                        if "mirror" in params:
                            mirror_image(reply)
                        if "flip" in params:
                            flip_image(reply)
                        if "transparent" in params:
                            make_transparent_image(reply)
                        if "convert-png" in params:
                            convert_image_to_png(reply)
                        if "convert-bmp" in params:
                            convert_image_to_bmp(reply)
                        if settings.ROTATE_COMMAND in params:
                            try:
                                rotate_image(reply,
                                             rotate_by_degrees=params[params.index(settings.ROTATE_COMMAND) + 1],
                                             rotation_type=params[params.index(settings.ROTATE_COMMAND) + 2])
                            except IndexError:
                                rotate_image(reply,
                                             rotate_by_degrees=params[params.index(settings.ROTATE_COMMAND) + 1])
                        reply_to_toot(reply.status_id)
            mastodon.notifications_clear()
            status_notifications.clear()
            bot_delete_files_in_directory(settings.INPUT_FOLDER)
            bot_delete_files_in_directory(settings.OUTPUT_FOLDER)
        schedule.run_pending()
        time.sleep(1)


def get_information_about_image(reply):
    for image in range(len(reply.media)):
        input_image = settings.JPEG_INPUT.format(image)
        img_open = cv2.imread(input_image)
        message = "Image properties: " \
                  "\n- Number of Pixels: " + str(img_open.size) \
                  + "\n- Shape/Dimensions: " + str(img_open.shape)
        reply_to_toot(reply.status_id, message=message)


def convert_image_using_pix2pix(reply):
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

        for image in range(len(reply.media)):
            try:
                image_path = str(settings.OUTPUT_FOLDER / "{}-outputs.png".format(image))
                reply_to_toot(reply.status_id, image_path=image_path)
                print("Tooting!")
            except ValueError as e:
                print("Something went wrong!")
                print(e.output)


def decolourise_image(reply):
    for image in range(len(reply.media)):
        img_open = cv2.imread(settings.JPEG_INPUT.format(image))
        gray = cv2.cvtColor(img_open, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(settings.JPEG_INPUT.format(image), gray)
        print("decolourise_image")

def display_colour_channel(reply, colour):
    colour = colour()
    for image in range(len(reply.media)):
        image_open = cv2.imread(settings.JPEG_INPUT.format(image))
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
        cv2.imwrite(settings.JPEG_OUTPUT.format(image), temp_image)


def get_text_from_image(reply):
    for image in range(len(reply.media)):
        # TODO: Look into removing this hardcoded path
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
        img = cv2.imread(settings.JPEG_INPUT.format(image))
        text = pytesseract.image_to_string(img)


def check_image_type(filepath):
    filepath_with_jpeg = str(filepath + ".jpeg")
    if not is_jpg(filepath):
        im = Image.open(filepath)
        rgb_image = im.convert('RGB')
        rgb_image.save(filepath_with_jpeg)
    else:
        os.renames(str(filepath), filepath_with_jpeg)


def rotate_image(reply, rotate_by_degrees=None, rotation_type=None):
    for image in range(len(reply.media)):
        image_open = cv2.imread(settings.JPEG_INPUT.format(image))
        if str(rotation_type) == settings.ROTATE_SIMPLE:
            rotated = imutils.rotate(image_open, int(rotate_by_degrees))
        else:
            rotated = imutils.rotate_bound(image_open, int(rotate_by_degrees))
        cv2.imwrite(settings.JPEG_INPUT.format(image), rotated)
        print("rotated")


def combine_image(filepath1, filepath2=None):
    if filepath2 is None:
        filepath2 = filepath1
    img1 = Image.open(filepath1)
    img2 = Image.open(filepath2)
    images = [img1, img2]
    combined_image = append_images(images, direction="horizontal")
    combined_image.save(filepath1)


def show_image_histogram(reply):
    for image in range(len(reply.media)):
        input_image = cv2.imread(settings.JPEG_INPUT.format(image))
        color = ('b', 'g', 'r')
        for i, col in enumerate(color):
            histogram = cv2.calcHist([input_image], [i], None, [256], [0, 256])
            plt.plot(histogram, color=col)
            plt.xlim([0, 256])
        plt.draw()
        plt.savefig(settings.JPEG_OUTPUT.format(image), bbox_inches='tight')
        reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image),
                      message="Histogram")


def create_border(reply):
    for image in range(len(reply.media)):
        input_image = cv2.imread(settings.JPEG_INPUT.format(image))
        input_image = cv2.copyMakeBorder(input_image, 10, 10, 10, 10, cv2.BORDER_REFLECT)
        cv2.imwrite(settings.JPEG_OUTPUT.format(image), input_image)
        reply_to_toot(reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image)))


def crop_image(reply):
    for image in range(len(reply.media)):
        img = Image.open(settings.JPEG_INPUT.format(image))
        width, height = img.size

        # TODO: Change these to make them user generated
        left = 5
        top = height / 4
        right = 164
        bottom = 3 * height / 4

        cropped_img = img.crop((left, top, right, bottom))
        cropped_img.save(settings.JPEG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image),
                      message="Here is your cropped image")


def enhance_image(reply):
    for image in range(len(reply.media)):
        img = Image.open(settings.JPEG_INPUT.format(image))
        enhancer = ImageEnhance.Sharpness(img)
        img_enhanced = enhancer.enhance(10.0)
        img_enhanced.save(settings.JPEG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image))


def adjust_brightness(reply, value=1.5):
    value = float(value)
    for image in range(len(reply.media)):
        img = Image.open(settings.JPEG_INPUT.format(image))
        enhancer = ImageEnhance.Brightness(img)
        img_enhanced = enhancer.enhance(value)
        img_enhanced.save(settings.JPEG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image))


def adjust_contrast(reply, value=1.5):
    value = float(value)
    for image in range(len(reply.media)):
        img = Image.open(settings.JPEG_INPUT.format(image))
        enhancer = ImageEnhance.Contrast(img)
        img_enhanced = enhancer.enhance(value)
        img_enhanced.save(settings.JPEG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image))


def adjust_colour(reply, value=1.5):
    value = float(value)
    for image in range(len(reply.media)):
        img = Image.open(settings.JPEG_INPUT.format(image))
        enhancer = ImageEnhance.Color(img)
        img_enhanced = enhancer.enhance(value)
        img_enhanced.save(settings.JPEG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image))


def flip_image(reply):
    for image in range(len(reply.media)):
        img = Image.open(settings.JPEG_INPUT.format(image))
        img_flipped = ImageOps.flip(img)
        img_flipped.save(settings.JPEG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image))


def mirror_image(reply):
    for image in range(len(reply.media)):
        img = Image.open(settings.JPEG_INPUT.format(image))
        img_mirrored = ImageOps.mirror(img)
        img_mirrored.save(settings.JPEG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.JPEG_OUTPUT.format(image))


def make_transparent_image(reply):
    for image in range(len(reply.media)):
        img_transparent = Image.open(settings.JPEG_INPUT.format(image))
        img_transparent.putalpha(128)
        img_transparent.save(settings.PNG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.PNG_OUTPUT.format(image))


# def give_title(status_notifications):
#     for reply in status_notifications:
#         for image in range(len(reply.media)):


def convert_image_to_png(reply):
    for image in range(len(reply.media)):
        Image.open(settings.JPEG_INPUT.format(image)).save(settings.PNG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.PNG_OUTPUT.format(image))


def convert_image_to_bmp(reply):
    for image in range(len(reply.media)):
        Image.open(settings.JPEG_INPUT.format(image)).save(settings.PNG_OUTPUT.format(image))
        reply_to_toot(reply.status_id, image_path=settings.BMP_OUTPUT.format(image))


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


def clear_notifications():
    mastodon.notifications_clear()


def strip_tags(html):
    s = html_stripper.MLStripper()
    s.feed(html)
    return s.get_data()

