import datetime
import glob
import os
import re
import shutil
import threading
import time
import urllib.request
from pathlib import Path

import cv2
import imutils
import pytesseract
import requests
import schedule
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw, ImageFont
from dotenv import load_dotenv
from mastodon import Mastodon
from matplotlib import pyplot as plt

import html_stripper
import settings

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


def reply_to_toot(post_id, account_name, message=None, status_notifications=None):
    media_ids = []
    for fn in os.listdir(str(settings.INPUT_FOLDER)):
        if fn.endswith(('.jpeg', '.png')):
            print(Path(fn))
            image_dict = mastodon.media_post(str(settings.INPUT_FOLDER / fn))
            media_ids.append(image_dict["id"])
    if message is not None:
        parts = []
        total_len = str(len(message) // settings.MAX_MESSAGE_LENGTH)
        count = 1
        split_lines = message.splitlines(True)
        while split_lines:
            message_part = "@" + account_name + " {}/".format(count) + total_len + "\n\n"
            while split_lines != [] and len(message_part) + len(split_lines[0]) < settings.MAX_MESSAGE_LENGTH:
                message_part += split_lines[0]
                split_lines = split_lines[1:]
            parts.append(message_part)
            count += 1
        for part in parts:
            print(part)
            post_id = mastodon.status_post(status=part, media_ids=media_ids, in_reply_to_id=post_id)
    else:
        while media_ids:
            mastodon.status_post(status=message, media_ids=media_ids[0:4], in_reply_to_id=post_id)
            media_ids = media_ids[4:]


def toot_image_of_the_day():
    r = requests.get(settings.NASA_ADDRESS_IMAGES % os.getenv("NASA"))
    json = r.json()
    print(json)
    urllib.request.urlretrieve(json["hdurl"], settings.DAILY_IMAGE)
    image_dict = mastodon.media_post(settings.DAILY_IMAGE)
    message = "Here is today's image!"
    mastodon.status_post(status=message, media_ids=image_dict["id"])


def get_trends():
    try:
        r = requests.get("%s/api/v1/trends/" % settings.BASE_ADDRESS)
        trends = r.json()
        print(trends)
    except ValueError:
        print(settings.JSON_ERROR_MESSAGE)


class UserNotification:
    def __init__(self, account_id, user_id, status_id, content, params):
        self.account_id = account_id
        self.user_id = user_id
        self.status_id = status_id
        self.content = content
        self.params = params
        self.media = []
        self.alt_text = []


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
        if self.users_who_have_made_requests[account_id] >= settings.MAX_REQUESTS_PER_HOUR:
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
        reply_message = ""
        for n in notifications:
            if n["type"] == "mention":
                account_id = n["account"]["id"]
                account_name = n["account"]["acct"]
                status_id = n["status"]["id"]
                content = n["status"]["content"]
                pattern = re.compile('[^a-zA-Z]')
                content = strip_tags(content).replace(settings.USERNAME, "").lower()
                pattern.sub("", content)
                params = content.split(" ")
                print(params)
                user = UserNotification(account_id, account_name, status_id, content, params)
                media = n["status"]["media_attachments"]
                if not spam_defender.allow_account_to_make_request(account_id):
                    reply_to_toot(status_id, message=settings.TOO_MANY_REQUESTS_MESSAGE, account_name=account_name)
                    print("Denied!")
                else:
                    for m in media:
                        if m["type"] == "image":
                            media_url = m["url"]
                            media_path = "{}".format(count)
                            urllib.request.urlretrieve(media_url, (str(settings.INPUT_FOLDER / media_path)))
                            reply_message += check_image_type(str(settings.INPUT_FOLDER / media_path))
                            user.media.append(media)
                            count += 1
                        else:
                            reply_message += settings.GIF_MESSAGE
                    status_notifications.append(user)
                    spam_defender.add_user_to_requests(user.account_id)
                count = 0
                num_files = os.listdir(str(settings.INPUT_FOLDER))
                if len(num_files) != 0 or "help" or "formats" in params:
                    for reply in status_notifications:
                        print(reply.params)
                        while params:

                            if params and params[0] == "help":
                                reply_message += settings.HELP_MESSAGE
                                params = params[1:]

                            if params and params[0] == "formats":
                                reply_message += settings.SUPPORTED_FORMATS_MESSAGE
                                params = params[1:]

                            if params and params[0] == 'decolourise' or params and params[0] == 'decolorize':
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    decolourise_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "text":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    reply_message += get_text_from_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "about":
                                count = 1
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    reply_message += get_information_about_image(input_image[0], count)
                                    count += 1
                                params = params[1:]

                            if params and params[0] == "preserve":
                                try:
                                    if params[params.index("preserve") + 1] not in settings.SET_OF_COLOURS:
                                        reply_message += "\nColour channel error: Invalid colour!"
                                    else:
                                        for image in range(len(reply.media)):
                                            input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                            display_colour_channel(input_image[0],
                                                                   params[params.index("preserve") + 1])
                                            params = params[2:]
                                except IndexError:
                                    reply_message += "\nYou didn't specify a colour for your colour channel"
                                    params = params[1:]

                            if params and params[0] == "histogram":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    show_image_histogram(input_image[0])
                                params = params[1:]

                            if params and params[0] == "crop":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    try:
                                        reply_message += crop_image(input_image[0],
                                                                    left=params[1],
                                                                    right=params[2],
                                                                    top=params[3],
                                                                    bottom=params[4])
                                        params = params[5:]
                                    except IndexError:
                                        reply_message += "\nCrop failed!"
                                        params = params[1:]
                                    except TypeError:
                                        reply_message += "\nCrop failed!"
                                        params = params[1:]

                            if params and params[0] == "enhance":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    enhance_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "brightness":
                                    for image in range(len(reply.media)):
                                        try:
                                            input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                            adjust_brightness(input_image, value=params[1])
                                            params = params[2:]
                                        except IndexError:
                                            adjust_brightness(reply)
                                            params = params[1:]

                            if params and params[0] == "contrast":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    try:
                                        adjust_contrast(input_image[0], value=params[1])
                                        params = params[2:]
                                    except IndexError:
                                        adjust_contrast(input_image[0])
                                        params = params[1:]

                            if params and params[0] == "colour":
                                for image in range(len(reply.media)):
                                    try:
                                        adjust_colour(settings.IMAGE_INPUT.format(image), value=params[1])
                                        params = params[2:]
                                    except IndexError:
                                        adjust_contrast(settings.IMAGE_INPUT.format(image))
                                        params = params[1:]

                            if params and params[0] == "mirror":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    mirror_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "flip":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    flip_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "transparent":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    make_transparent_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "negative":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    make_negative_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "sepia":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    make_sepia_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "blur":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    blur_image(input_image[0])
                                params = params[1:]

                            if params and params[0] == "blurred":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    blur_edges(input_image[0])
                                params = params[1:]

                            if params and params[0] == "border":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    add_border(input_image[0])
                                params = params[1:]

                            if params and params[0] == "reflective" and params[1] == "border":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    create_reflective_border(input_image[0])
                                params = params[2:]

                            if params and params[0] == "png":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    convert_image_to_png(input_image[0])
                                params = params[1:]

                            if params and params[0] == "bmp":
                                for image in range(len(reply.media)):
                                    input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                    convert_image_to_bmp(input_image[0])
                                params = params[1:]

                            if params and params[0] == "watermark":
                                try:
                                    for image in range(len(reply.media)):
                                        input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                        add_watermarks(input_image[0],
                                                       wm_text=params[1])
                                        params = params[2:]
                                except IndexError:
                                    reply_message += "\nNo watermark specified"

                            if params and params[0] == "rotate":
                                try:
                                    for image in range(len(reply.media)):
                                        remove_params = 0
                                        input_image = glob.glob(settings.IMAGE_INPUT.format(image))
                                        if len(params) >= 3 and params[2] == "simple" and params != []:
                                            rotate_image(input_image[0],
                                                         rotate_by_degrees=params[1],
                                                         rotation_type=params[2])
                                            remove_params = 3
                                        else:
                                            rotate_image(input_image[0],
                                                         rotate_by_degrees=params[1])
                                            remove_params = 2
                                    params = params[remove_params:]
                                except IndexError:
                                    reply_message += "\nYou didn't specify how many degrees you wanted it rotated " \
                                                     "by "
                                    params = params[1:]

                            elif params:
                                if params[0] not in settings.SET_OF_COMMANDS:
                                    reply_message += settings.INVALID_COMMAND.format(params[0])
                                    params = params[1:]

                        reply_to_toot(reply.status_id, message="\n" + str(reply_message),
                                      account_name=account_name, status_notifications=status_notifications)
            mastodon.notifications_clear()
            status_notifications.clear()
            bot_delete_files_in_directory(settings.INPUT_FOLDER)
            reply_message = ""
        schedule.run_pending()
        time.sleep(1)


def get_information_about_image(input_image, count):
    img_open = cv2.imread(input_image)
    message = "\n\nImage {} properties: " \
              "\n- Number of Pixels: " + str(img_open.size) \
              + "\n- Shape/Dimensions: " + str(img_open.shape).format(count)
    return message


def decolourise_image(input_image):
    img_open = cv2.imread(input_image)
    gray = cv2.cvtColor(img_open, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(input_image, gray)


def display_colour_channel(input_image, colour):
    img = cv2.imread(input_image)
    temp_image = img.copy()
    if colour == "red":
        temp_image[:, :, 0] = 0
        temp_image[:, :, 1] = 0
    if colour == "green":
        temp_image[:, :, 0] = 0
        temp_image[:, :, 2] = 0
    if colour == "blue":
        temp_image[:, :, 1] = 0
        temp_image[:, :, 2] = 0
    cv2.imwrite(input_image, temp_image)


def get_text_from_image(input_image):
    img = cv2.imread(input_image)
    text = pytesseract.image_to_string(img)
    return text


def check_image_type(filepath):
    img = Image.open(filepath)
    img_format = img.format
    user_message = ""
    if img_format == "GIF":
        os.remove(filepath)  # Mastodon uses MP4 for gifs, but in case one slips through.
        user_message += settings.GIF_MESSAGE  # Informs the user.
    if img_format == "JPEG":  # If the file is JPEG, give it a JPEG extension.
        os.renames(str(filepath), str(filepath + ".jpeg"))
    if img_format == "PNG":  # If the file is PNG, give it a PNG extension.
        os.renames(str(filepath), str(filepath + ".png"))
    if img_format == "BMP":  # Mastodon does not currently support TIFF
        os.renames(str(filepath), str(filepath + ".bmp"))
    if img_format == "TIFF":  # Mastodon does not currently support TIFF
        os.renames(str(filepath), str(filepath + ".tiff"))
    return user_message


def rotate_image(input_image, rotate_by_degrees=None, rotation_type=None):
    image_open = cv2.imread(input_image)
    if str(rotation_type) == settings.ROTATE_SIMPLE:
        rotated = imutils.rotate(image_open, int(rotate_by_degrees))
    else:
        rotated = imutils.rotate_bound(image_open, int(rotate_by_degrees))
    cv2.imwrite(input_image, rotated)


def combine_image(filepath1, filepath2=None):
    if filepath2 is None:
        filepath2 = filepath1
    img1 = Image.open(filepath1)
    img2 = Image.open(filepath2)
    images = [img1, img2]
    combined_image = append_images(images, direction="horizontal")
    combined_image.save(filepath1)


def show_image_histogram(input_image):
    img = cv2.imread(input_image)
    color = ('b', 'g', 'r')
    for i, col in enumerate(color):
        histogram = cv2.calcHist([img], [i], None, [256], [0, 256])
        plt.plot(histogram, color=col)
        plt.xlim([0, 256])
    plt.draw()
    plt.savefig(input_image, bbox_inches='tight')


def create_reflective_border(input_image):
    img = cv2.imread(input_image)
    img = cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_REFLECT)
    cv2.imwrite(input_image, img)


def crop_image(input_image, left, top, right, bottom):
    img = Image.open(input_image)
    width, height = img.size
    status_message = ""
    try:
        left = int(left)
        top = int(top)
        right = int(right)
        bottom = int(bottom)
    except ValueError:
        return "Please supply integers in the format crop <int> <int> <int> <int>"

    if top > height or top < 0:
        status_message += settings.CROP_OUT_OF_RANGE.format("top", height)
    if left > width or left < 0:
        status_message += settings.CROP_OUT_OF_RANGE.format("left", width)
    if right > width or right < 0:
        status_message += settings.CROP_OUT_OF_RANGE.format("right", width)
    if bottom > height or bottom < 0:
        status_message += settings.CROP_OUT_OF_RANGE.format("bottom", width)

    if status_message != "":
        return status_message

    cropped_img = ImageOps.crop(img, (left, top, right, bottom))
    cropped_img.save(input_image)


def enhance_image(input_image):
    img = Image.open(input_image)
    enhancer = ImageEnhance.Sharpness(img)
    img_enhanced = enhancer.enhance(10.0)
    img_enhanced.save(input_image)


def adjust_brightness(input_image, value=1.5):
    value = float(value)
    img = Image.open(input_image)
    enhancer = ImageEnhance.Brightness(img)
    img_enhanced = enhancer.enhance(value)
    img_enhanced.save(input_image)


def adjust_contrast(input_image, value=1.5):
    value = float(value)
    img = Image.open(input_image)
    enhancer = ImageEnhance.Contrast(img)
    img_enhanced = enhancer.enhance(value)
    img_enhanced.save(input_image)


def adjust_colour(input_image, value=1.5):
    value = float(value)
    img = Image.open(input_image)
    enhancer = ImageEnhance.Color(img)
    img_enhanced = enhancer.enhance(value)
    img_enhanced.save(input_image)


def flip_image(input_image):
    img = Image.open(input_image)
    img_flipped = ImageOps.flip(img)
    img_flipped.save(input_image)


def mirror_image(input_image):
    img = Image.open(input_image)
    img_mirrored = ImageOps.mirror(img)
    img_mirrored.save(input_image)


def make_transparent_image(input_image):
    img_transparent = Image.open(input_image)
    img_transparent.putalpha(128)
    img_transparent.save(settings.PNG_OUTPUT)


def make_negative_image(input_image):
    img = Image.open(input_image)
    negative_img = Image.new('RGB', img.size)
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            r, g, b = img.getpixel((x, y))
            negative_img.putpixel((x, y), (255 - r, 255 - g, 255 - b))
    negative_img.save(input_image)


def make_sepia_image(input_image):
    img = Image.open(input_image)
    sepia_img = Image.new('RGB', img.size)
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            r, g, b = img.getpixel((x, y))
            red = int(r * 0.393 + g * 0.769 + b * 0.189)
            green = int(r * 0.349 + g * 0.686 + b * 0.168)
            blue = int(r * 0.272 + g * 0.534 + b * 0.131)
            sepia_img.putpixel((x, y), (red, green, blue))
    sepia_img.save(input_image)


def blur_image(input_image):
    img = Image.open(input_image)
    blurred_image = img.filter(ImageFilter.BoxBlur(5))
    blurred_image.save(input_image)


def blur_edges(input_image):
    radius, diameter = 20, 40
    img = Image.open(input_image)  # Paste image on white background
    background_size = (img.size[0] + diameter, img.size[1] + diameter)
    background = Image.new('RGB', background_size, (255, 255, 255))
    background.paste(img, (radius, radius))  # create new images with white and black
    mask_size = (img.size[0] + diameter, img.size[1] + diameter)
    mask = Image.new('L', mask_size, 255)
    black_size = (img.size[0] - diameter, img.size[1] - diameter)
    black = Image.new('L', black_size, 0)  # create blur mask
    mask.paste(black, (diameter, diameter))  # Blur image and paste blurred edge according to mask
    blur = background.filter(ImageFilter.GaussianBlur(radius / 2))
    background.paste(blur, mask=mask)
    background.save(input_image)


# TODO: Change this so user can chnage colour
def add_border(input_image):
    img = Image.open(input_image)
    colour = "white"
    border = (20, 10, 20, 10)
    bordered_img = ImageOps.expand(img, border=border, fill=colour)
    bordered_img.save(input_image)


def add_watermarks(input_image, wm_text):
    img = Image.open(input_image)  # open image to apply watermark to
    img.convert("RGB")  # get image size
    img_width, img_height = img.size  # 5 by 4 water mark grid
    wm_size = (int(img_width * 0.20), int(img_height * 0.25))
    wm_txt = Image.new("RGBA", wm_size, (255, 255, 255, 0))  # set text size, 1:40 of the image width
    font_size = int(img_width / 40)  # load font e.g. gotham-bold.ttf
    font = ImageFont.truetype(str(settings.BASE_DIRECTORY / "resources" / "Gotham-Bold.ttf"), font_size)
    d = ImageDraw.Draw(wm_txt)
    left = (wm_size[0] - font.getsize(wm_text)[0]) / 2
    top = (wm_size[1] - font.getsize(wm_text)[1]) / 2  # RGBA(0, 0, 0, alpha) is black
    # alpha channel specifies the opacity for a colour
    alpha = 75  # write text on blank wm_text image
    d.text((left, top), wm_text, fill=(0, 0, 0, alpha), font=font)  # uncomment to rotate watermark text
    wm_txt = wm_txt.rotate(15, expand=1)
    wm_txt = wm_txt.resize(wm_size, Image.ANTIALIAS)
    for i in range(0, img_width, wm_txt.size[0]):
        for j in range(0, img_height, wm_txt.size[1]):
            img.paste(wm_txt, (i, j), wm_txt)  # save image with watermark
    img.save(input_image)  # show image with watermark in preview


def convert_image_to_png(input_image):
    Image.open(input_image).save(settings.PNG_OUTPUT)


def convert_image_to_bmp(input_image):
    Image.open(input_image).save(settings.BMP_OUTPUT)


def append_images(images, direction='horizontal',
                  bg_color=(255, 255, 255), aligment='center'):
    widths, heights = zip(*(i.size for i in images))

    if direction == 'horizontal':
        new_width = sum(widths)
        new_height = max(heights)
    else:
        new_width = max(widths)
        new_height = sum(heights)

    img = Image.new('RGB', (new_width, new_height), color=bg_color)

    offset = 0
    for im in images:
        if direction == 'horizontal':
            y = 0
            if aligment == 'center':
                y = int((new_height - im.size[1]) / 2)
            elif aligment == 'bottom':
                y = new_height - im.size[1]
            img.paste(im, (offset, y))
            offset += im.size[0]
        else:
            x = 0
            if aligment == 'center':
                x = int((new_width - im.size[0]) / 2)
            elif aligment == 'right':
                x = new_width - im.size[0]
            img.paste(im, (x, offset))
            offset += im.size[1]
    return img


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
            print("Failed to delete {}. Reason: {}".format(filename, e))


def clear_notifications():
    mastodon.notifications_clear()


def strip_tags(html):
    s = html_stripper.MLStripper()
    s.feed(html)
    return s.get_data()
