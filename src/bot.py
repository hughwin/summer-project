import datetime
import glob
import os
import random
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
from textblob import TextBlob

import html_stripper
import settings
from image_recognition import ImageRecognition

load_dotenv()  # Important variables such as my secret key are stored in a .env file.

#   Set up Mastodon
mastodon = Mastodon(
    access_token=os.getenv("ACCESS_TOKEN"),
    api_base_url=settings.BASE_ADDRESS
)


def start_bot():
    """
    Starts the bot. Generates a class of SpamDefender and starts it on a separate thread,
    and then starts the main listener thread.
    """
    spam_defender = SpamDefender()
    spam_defender.start()

    listener = threading.Thread(target=listen_to_request(spam_defender))
    listener.start()


def reply_to_toot(post_id, account_name, message=None):
    """Replies to the calling user with their modified images.

    :param post_id: the post id that the bot is replying to
    :param account_name: the account name that the bot is replying to
    :param message: the informative message that is included in the reply toot.
    """
    media_ids = []
    for fn in os.listdir(str(settings.INPUT_FOLDER)):
        if fn.endswith(('.jpeg', '.png')):
            print(Path(fn))
            image_dict = mastodon.media_post(str(settings.INPUT_FOLDER / fn), description="Requested modified image")
            media_ids.append(image_dict["id"])
    if message is not None:
        parts = []
        total_len = str(len(message) // settings.MAX_MESSAGE_LENGTH + 1)
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
    """Method to toot a daily picture of the universe.

    This function exists to toot a picture of the universe to the instance the bot is running on. This is done to
    advertise the bot and to give users who are using the bot (maybe for the first time) the confidence that the bot
    is still running.
    """
    try:
        r = requests.get(settings.NASA_ADDRESS_IMAGES % os.getenv("NASA"))
        json = r.json()
        urllib.request.urlretrieve(json["hdurl"], settings.DAILY_IMAGE)
        description = json["title"]
        image_dict = mastodon.media_post(settings.DAILY_IMAGE, description=description)
        print(image_dict)
        message = "Here is today's image! " + description
        mastodon.status_post(status=message, media_ids=image_dict)
    except requests.exceptions.RequestException as e:
        print(e)


class UserNotification:
    """Convenience class to hold requesting user's data.


    Whilst this call is not strictly required, as all of the data is collected in notification dictionary
    returned from Mastodon, this class just collects all the important used parts together in one place.

    :param account_id: The account ID of the requesting user
    :param user_id: the user ID of the requesting user
    :param status_id: the status ID of the requesting user
    :param content: the content (message) sent to the bot
    :param params: the content with HTML tags removed.
    """

    def __init__(self, account_id, user_id, status_id, content, params):
        self.account_id = account_id
        self.user_id = user_id
        self.status_id = status_id
        self.content = content
        self.params = params
        self.media = []
        self.alt_text = []


class SpamDefender(threading.Thread):
    """Basic spam protection from users making too many requests to the bot.


    This class checks to see how many user requests have been made in the last hour by a particular user.
    If the number if requests exceeds the number of requests allowed in settings.py (MAX_REQUESTS_PER_HOUR)
    the bot denies that user from making any more requests. The requesting users are cleared each hour.
    """

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
        """
        Adds the user to the users_who_have_made_requests dictionary.
        :param account_id: id of the account making the request
        """
        if account_id in self.users_who_have_made_requests:
            self.users_who_have_made_requests[account_id] += 1
        else:
            self.users_who_have_made_requests[account_id] = 1

    def allow_account_to_make_request(self, account_id):
        """
         Determines whether a user is able to make a request.
         :param account_id: id of the account making the request
         :return : boolean
         """
        if account_id not in self.users_who_have_made_requests:
            return True
        if self.users_who_have_made_requests[account_id] >= settings.MAX_REQUESTS_PER_HOUR:
            return False
        else:
            return True


def listen_to_request(spam_defender):
    """The main loop of the program.

    Intentional infinite loop that constantly checks to see whether requests have been made by users. If they have,
    it first checks that the user hasn't made too many requests. It then parses the input of the message,
    and controls the resultant manipulation of the image. Before returning the manipulated image to the user.

    Also controls the tooting of images from the NASA API.

    :param spam_defender: an instance of the SpamDefender class

    """
    file_count = 0
    status_notifications = []

    image_recognition = ImageRecognition()
    image_recognition.setup()

    schedule.every().day.at("10:30").do(toot_image_of_the_day)

    while True:
        print("Checking notifications!")
        notifications = mastodon.notifications(mentions_only=True)

        for n in notifications:
            if n["type"] == "mention":

                account_id = n["account"]["id"]
                account_name = n["account"]["acct"]
                status_id = n["status"]["id"]

                content = n["status"]["content"]
                content = strip_tags(content).replace(settings.USERNAME, "").lower()
                content = re.sub('[^a-zA-Z0-9]', " ", content)  # Removes all non-alphanumeric characters

                params = content.split(" ")
                user = UserNotification(account_id, account_name, status_id, content, params)
                media = n["status"]["media_attachments"]

                reply_message_set = set()
                about_list = []

                if not spam_defender.allow_account_to_make_request(account_id):
                    reply_to_toot(status_id, message=settings.TOO_MANY_REQUESTS_MESSAGE, account_name=account_name)
                    print("Denied!")
                else:
                    for m in media:
                        if m["type"] == "image":
                            media_url = m["url"]
                            media_path = "{}".format(file_count)
                            urllib.request.urlretrieve(media_url, (str(settings.INPUT_FOLDER / media_path)))
                            reply_message_set.add(check_image_type(str(settings.INPUT_FOLDER / media_path)))
                            user.media.append(media)
                            file_count += 1
                        else:
                            reply_message_set.add(settings.GIF_MESSAGE)
                    status_notifications.append(user)
                    spam_defender.add_user_to_requests(user.account_id)
                file_count = 0
                num_files = os.listdir(str(settings.INPUT_FOLDER))
                if len(num_files) != 0 or "help" in params or "formats" in params:

                    sentiment_list = []

                    for reply in status_notifications:
                        os.chdir(str(settings.INPUT_FOLDER))
                        image_glob = glob.glob(settings.IMAGE_INPUT.format("*.png")) \
                                     + glob.glob(settings.IMAGE_INPUT.format("*.jpeg"))
                        print(image_glob)

                        about_count = 1

                        while params:
                            print(params)

                            if params and params[0] == "formats":
                                reply_message_set.add(settings.SUPPORTED_FORMATS_MESSAGE)
                                params = params[1:]

                            if params and params[0] == 'decolourise' or params and params[0] == 'decolorize':
                                for image in image_glob:
                                    reply_message_set.add(decolourise_image(image))
                                params = params[1:]

                            if params and params[0] == "text":
                                for image in image_glob:
                                    reply_message_set.add(get_text_from_image(image))
                                params = params[1:]

                            if params and params[0] == "about":
                                for image in image_glob:
                                    about_list.append(get_information_about_image(image, about_count))
                                    about_count += 1
                                params = params[1:]

                            if params and params[0] == "preserve":
                                try:
                                    for image in image_glob:
                                        reply_message_set.add(display_colour_channel(image,
                                                                                     params[
                                                                                         params.index("preserve") + 1]))
                                    params = params[2:]
                                except IndexError:
                                    reply_message_set.add(settings.OPERATION_FAILED_MESSAGE.format("preserve colour") +
                                                          "You didn't specify a colour for your colour channel\n")
                                    params = params[1:]

                            if params and params[0] == "histogram":
                                for image in image_glob:
                                    show_image_histogram(image)
                                params = params[1:]

                            if params and params[0] == "crop":
                                remove_params = 0
                                for image in image_glob:
                                    try:
                                        reply_message_set.add(crop_image(image,
                                                                         left=params[1],
                                                                         right=params[2],
                                                                         top=params[3],
                                                                         bottom=params[4]))
                                        remove_params = 5
                                    except (IndexError, ValueError):
                                        reply_message_set.add(settings.OPERATION_FAILED_MESSAGE.format("crop"))
                                        remove_params = 1
                                params = params[remove_params:]

                            if params and params[0] == "enhance":
                                for image in image_glob:
                                    reply_message_set.add(enhance_image(image))
                                params = params[1:]

                            if params and params[0] == "brightness":
                                for image in image_glob:
                                    try:
                                        reply_message_set.add(adjust_brightness(image, value=float(params[1])))
                                        params = params[2:]
                                    except (IndexError, ValueError):
                                        reply_message_set.add(adjust_contrast(image))
                                        params = params[1:]

                            if params and params[0] == "contrast":
                                for image in range(len(reply.media)):
                                    try:
                                        reply_message_set.add(adjust_contrast(image, value=float(params[1])))
                                        params = params[2:]
                                    except (IndexError, ValueError):
                                        reply_message_set.add(adjust_contrast(image))
                                        params = params[1:]

                            if params and params[0] == "colour":
                                for image in image_glob:
                                    try:
                                        reply_message_set.add(adjust_colour(image, value=float(params[1])))
                                        params = params[2:]
                                    except (IndexError, ValueError):
                                        reply_message_set.add(adjust_contrast(image))
                                        params = params[1:]

                            if params and params[0] == "mirror":
                                for image in image_glob:
                                    reply_message_set.add(mirror_image(image))
                                params = params[1:]

                            if params and params[0] == "flip":
                                for image in image_glob:
                                    reply_message_set.add(flip_image(image))
                                params = params[1:]

                            if params and params[0] == "transparent":
                                for image in image_glob:
                                    reply_message_set.add(make_transparent_image(image))
                                params = params[1:]

                            if params and params[0] == "negative":
                                for image in image_glob:
                                    reply_message_set.add(make_negative_image(image))
                                params = params[1:]

                            if params and params[0] == "sepia":
                                for image in image_glob:
                                    reply_message_set.add(make_sepia_image(image))
                                params = params[1:]

                            if params and params[0] == "blur":
                                for image in image_glob:
                                    reply_message_set.add(blur_image(image))
                                params = params[1:]

                            if params and params[0] == "blurred":
                                for image in image_glob:
                                    reply_message_set.add(blur_edges(image))
                                params = params[1:]

                            if params and params[0] == "border":
                                for image in image_glob:
                                    reply_message_set.add(add_border(image))
                                params = params[1:]

                            if params and params[0] == "reflective" and params[1] == "border":
                                for image in image_glob:
                                    reply_message_set.add(create_reflective_border(image))
                                params = params[2:]

                            if params and params[0] == "png":
                                for image in image_glob:
                                    reply_message_set.add(convert_image_to_png(image))
                                params = params[1:]

                            if params and params[0] == "jpeg":
                                for image in image_glob:
                                    reply_message_set.add(convert_image_to_jpeg(image))
                                params = params[1:]

                            if params and params[0] == "watermark":
                                try:
                                    for image in image_glob:
                                        reply_message_set.add(add_watermarks(image,
                                                                             wm_text=params[1]))
                                        params = params[2:]
                                except IndexError:
                                    reply_message_set.add("\nNo watermark specified")

                            if params and params[0] == "rotate":
                                try:
                                    remove_params = 0
                                    for image in image_glob:
                                        if len(params) >= 4:
                                            if params[2] == "left" or params[2] == "right" and \
                                                    params[3] == "simple" and params != []:
                                                reply_message_set.add(rotate_image(image,
                                                                                   rotate_by_degrees=params[1],
                                                                                   rotation_direction=params[2],
                                                                                   rotation_type=params[3]))
                                            remove_params = 4
                                        elif len(params) >= 3:
                                            if params[2] == "left" or params[2] == "left":
                                                reply_message_set.add(rotate_image(image,
                                                                                   rotate_by_degrees=params[1],
                                                                                   rotation_direction=params[2]))
                                                remove_params = 3
                                        elif params:
                                            reply_message_set.add(rotate_image(image, rotate_by_degrees=params[1]))
                                            remove_params = 2
                                    params = params[remove_params:]
                                except (IndexError, ValueError):
                                    reply_message_set.add(settings.OPERATION_FAILED_MESSAGE.format("rotate")
                                                          + "You didn't specify how many degrees you wanted it"
                                                            " rotated by\n")

                            if params and params[0] == "append":
                                if len(params) >= 2:
                                    if params[1] == "vertical" or params[1] == "horizontal":
                                        reply_message_set.add(append_images(image_glob, direction=params[1]))
                                        params = params[2:]
                                else:
                                    reply_message_set.add(append_images(image_glob))
                                    params = params[1:]

                            if params and params[0] == "landmarks":
                                for image in image_glob:
                                    reply_message_set.add(image_recognition.detect_landmarks(image))
                                    params = params[1:]

                            if params and params[0] == "objects":
                                for image in image_glob:
                                    reply_message_set.add(image_recognition.localize_objects(image))
                                    params = params[1:]

                            if params and params[0] == "properties":
                                for image in image_glob:
                                    reply_message_set.add("Properties in the image\n\n:" +
                                                          image_recognition.detect_labels(image))
                                    params = params[1:]

                            elif params:
                                if params[0] not in settings.SET_OF_COMMANDS:
                                    reply_message_set.add(settings.INVALID_COMMAND.format("\"" + params[0] + "\""))
                                    sentiment_list.append(params[0] + " ")
                                    params = params[1:]
                        sentiment_message = (sentiment_analysis("".join(sentiment_list)) + "\n\n") \
                            if sentiment_list != [] else ""
                        reply_to_toot(reply.status_id, message="\n" + sentiment_message + "".join(about_list) + "".join(
                            reply_message_set),
                                      account_name=account_name)
                else:
                    for reply in status_notifications:
                        sentiment_message = (sentiment_analysis("".join(params)) + "\n\n") \
                            if params != [] else ""
                        reply_to_toot(reply.status_id, message="\n" + sentiment_message +
                                                               "\n No commands recognised. If you need "
                                                               "help, call \"@botbot.botsin.space help\"",
                                      account_name=account_name)
            mastodon.notifications_clear()
            status_notifications.clear()
            bot_delete_files_in_directory(settings.INPUT_FOLDER)
        schedule.run_pending()
        time.sleep(1)


def sentiment_analysis(text):
    """Reads a string and determines the sentiment of the string.

    :param text: string to be analysed.
    :return str: appropriate semantic response to the input text.
    """

    polarity = TextBlob(text)
    polarity_score = polarity.sentiment.polarity

    if polarity_score >= .35:
        return random.choice(settings.POSITIVE_RESPONSES)
    if .35 > polarity_score > -.35:
        return random.choice(settings.NEUTRAL_RESPONSES)
    else:
        return random.choice(settings.NEGATIVE_RESPONSES)


def get_information_about_image(input_image, count):
    """Returns information about the image as a string.

    :param input_image: str the image's file path.
    :return: str the number of pixels and the shape and dimensions of the image.
    """
    try:
        img_open = cv2.imread(input_image)
        message = "\n\nImage {} properties: ".format(count) + \
                  "\n- Number of Pixels: " + str(img_open.size) + \
                  "\n- Shape/Dimensions: " + str(img_open.shape) + "\n\n"
        return message
    except cv2.error as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("getting information about the image")


def decolourise_image(input_image):
    """Returns a decolourised (greyscale) version of the image.

    :param input_image: str the image's file path.
    :return: str stating whether the requested operation was successful or not. .
    """
    try:
        img_open = cv2.imread(input_image)
        gray = cv2.cvtColor(img_open, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(input_image, gray)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("decolourise")
    except cv2.error as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("decolourise")


def display_colour_channel(input_image, colour):
    """Returns version of the image with only one colour channel (Red, green, or blue).

    :param input_image: str the image's file path.
    :param colour: colour of channel to be preserved
    :return: str stating whether the requested operation was successful or not. .
    """
    try:
        if colour not in settings.SET_OF_COLOURS:
            return settings.OPERATION_FAILED_MESSAGE.format("preserve colour") + "colour" + colour + "not recognised \n"
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
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("preserve colour " + colour)
    except cv2.error as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("preserve colour " + colour)


def get_text_from_image(input_image):
    """Uses pytesseract to extract the text from the image and returns this as a string

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = cv2.imread(input_image)
        text = pytesseract.image_to_string(img)
        return "Text from image \n\n" + text
    except (pytesseract.TesseractError, pytesseract.TesseractNotFoundError) as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("get text from message \n\n")


def check_image_type(input_image):
    """
    Checks what type of image the image in the toot is, and gives it the correct file extension

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        with Image.open(input_image) as img:
            img_format = img.format
        user_message = ""
        if img_format == "GIF":
            os.remove(input_image)  # Mastodon uses MP4 for gifs, but in case one slips through.
            user_message += settings.GIF_MESSAGE  # Informs the user.
        if img_format == "JPEG":  # If the file is JPEG, give it a JPEG extension.
            os.renames(str(input_image), str(input_image + ".jpeg"))
        if img_format == "PNG":  # If the file is PNG, give it a PNG extension.
            os.renames(str(input_image), str(input_image + ".png"))
        if img_format == "BMP":  # Mastodon does not currently support TIFF
            os.renames(str(input_image), str(input_image + ".bmp"))
        if img_format == "TIFF":  # Mastodon does not currently support TIFF
            os.renames(str(input_image), str(input_image + ".tiff"))
        return user_message
    except OSError as e:
        print(e)
        return "Something went wrong with converting the image\n"


def rotate_image(input_image, rotate_by_degrees=None, rotation_direction="right", rotation_type=None):
    """Rotates the image by the given number of degrees and saves a copy of the image
    There are two rotation types, simple and complex: simple rotates the image without resizing, and (complex)
    resizes the borders accordingly.

    :param input_image: str the image's file path.
    :param rotate_by_degrees: str the number of degrees the image is to be rotated by
    :param rotation_direction: str which way the image is to be rotated left / right.
    :param rotation_type: str simple/complex. Simple rotates the image without adjusting the size of the original image.
    :return: str with text of image if operation successful. Error message if not.
    """
    rotate_by_degrees = rotate_by_degrees if rotation_direction == "right" \
        else str(0 - int(rotate_by_degrees))

    try:
        image_open = cv2.imread(input_image)
        if str(rotation_type) == settings.ROTATE_SIMPLE:
            rotated = imutils.rotate(image_open, int(rotate_by_degrees))
        else:
            rotated = imutils.rotate_bound(image_open, int(rotate_by_degrees))
        cv2.imwrite(input_image, rotated)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("rotate " + rotate_by_degrees)

    except cv2.error as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("rotate image")


def show_image_histogram(input_image):
    """ Currently unused method to produce histograms of the images sent to the bot.
    """
    img = cv2.imread(input_image)
    color = ('b', 'g', 'r')
    for i, col in enumerate(color):
        histogram = cv2.calcHist([img], [i], None, [256], [0, 256])
        plt.plot(histogram, color=col)
        plt.xlim([0, 256])
    plt.draw()
    plt.savefig(input_image, bbox_inches='tight')


def create_reflective_border(input_image):
    """Creates a reflective border around the edge of the image.

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = cv2.imread(input_image)
        img = cv2.copyMakeBorder(img, 10, 10, 10, 10, cv2.BORDER_REFLECT)
        cv2.imwrite(input_image, img)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("reflective border")
    except cv2.error as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("reflective border")


def crop_image(input_image, left, top, right, bottom):
    """Crops the image by the input amounts (left, top, right, bottom)

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
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

        cropped_img = ImageOps.crop(img, (left, top, right, bottom))
        cropped_img.save(input_image)

        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("Cropped by " + str(left) + " " + str(top)
                                                            + " " + str(right) + " " + str(bottom))

    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("cropping the image")


def enhance_image(input_image):
    """Creates and saves an enhanced version of the image

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = Image.open(input_image)
        enhancer = ImageEnhance.Sharpness(img)
        img_enhanced = enhancer.enhance(10.0)
        img_enhanced.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("enhance image")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("enhance image")


def adjust_brightness(input_image, value=1.5):
    """Creates and saves a brightened / darkened version of the image

    :param input_image: str the image's file path.
    :param value: optional value determining how much brighter or darker the image is.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        value = float(value)
        img = Image.open(input_image)
        enhancer = ImageEnhance.Brightness(img)
        img_enhanced = enhancer.enhance(value)
        img_enhanced.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("adjust brightness " + str(value))
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("adjust brightness")


def adjust_contrast(input_image, value=1.5):
    """Adjusts the contrast and saves that version of the image

    :param input_image: str the image's file path.
    :param value: optional value determining the change in contrast.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        value = float(value)
        img = Image.open(input_image)
        enhancer = ImageEnhance.Contrast(img)
        img_enhanced = enhancer.enhance(value)
        img_enhanced.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("adjust contrast " + str(value))
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("adjust contrast")


def adjust_colour(input_image, value=1.5):
    """Adjusts the colour in the image and saves that version of the image

    :param input_image: str the image's file path.
    :param value: optional value determining the change in contrast.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        value = float(value)
        img = Image.open(input_image)
        enhancer = ImageEnhance.Color(img)
        img_enhanced = enhancer.enhance(value)
        img_enhanced.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("adjust colour " + str(value))
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("adjust colour")


def flip_image(input_image):
    """Flips the image and saves the flipped version

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = Image.open(input_image)
        img_flipped = ImageOps.flip(img)
        img_flipped.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("flip message")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("flip message")


def mirror_image(input_image):
    """Mirrors the image and saves the mirrored version

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = Image.open(input_image)
        img_mirrored = ImageOps.mirror(img)
        img_mirrored.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("mirror image")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("mirror image")


def make_transparent_image(input_image):
    """Creates a transparent (PNG) version of the image and saves it.

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img_transparent = Image.open(input_image)
        img_transparent.putalpha(128)
        img_transparent.save(settings.PNG_OUTPUT)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("transparent image")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("transparent image")


def make_negative_image(input_image):
    """Creates a negative style version of the image and saves it

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = Image.open(input_image)
        negative_img = Image.new('RGB', img.size)  # creates new image
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                r, g, b = img.getpixel((x, y))  # gets a pixel at x , y coordinates
                negative_img.putpixel((x, y), (255 - r, 255 - g, 255 - b))  # puts the 'negative' version
                # of this pixel on the new image
        negative_img.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("negative")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("negative")


def make_sepia_image(input_image):
    """Creates a sepia style version of the image and saves it

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = Image.open(input_image)
        sepia_img = Image.new('RGB', img.size)  # creates new image
        for x in range(img.size[0]):
            for y in range(img.size[1]):
                r, g, b = img.getpixel((x, y))  # gets a pixel at x , y coordinates
                red = int(r * 0.393 + g * 0.769 + b * 0.189)  # changes the pixel colours accordingly
                green = int(r * 0.349 + g * 0.686 + b * 0.168)
                blue = int(r * 0.272 + g * 0.534 + b * 0.131)
                sepia_img.putpixel((x, y), (red, green, blue))  # saves the sepia version of this image
        sepia_img.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("sepia")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("sepia")


def blur_image(input_image):
    """Creates a blurred version of the image and saves it

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = Image.open(input_image)
        blurred_image = img.filter(ImageFilter.BoxBlur(5))
        blurred_image.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("blur")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("blur")


def blur_edges(input_image):
    """Blurs the borders of a given image.

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
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
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("blur edges")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("blur edges")


# TODO: Change this so user can change colour
def add_border(input_image):
    """Adds a border to the given image

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        img = Image.open(input_image)
        colour = "white"
        border = (20, 10, 20, 10)
        bordered_img = ImageOps.expand(img, border=border, fill=colour)
        bordered_img.save(input_image)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("add border")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("add border")


def add_watermarks(input_image, wm_text):
    """Creates a version of the image with the users requested water marks added and saves it

    :param input_image: str the image's file path.
    :param wm_text: str the text to be added to the watermark
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
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
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("add watermarks")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("add watermarks")


def convert_image_to_png(input_image):
    """Converts the image to PNG

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        Image.open(input_image).save(settings.PNG_OUTPUT)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("convert to PNG")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("convert to PNG")


def convert_image_to_jpeg(input_image):
    """Converts the image to JPEG

    :param input_image: str the image's file path.
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        Image.open(input_image).save(settings.JPEG_OUTPUT)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("convert to jpeg")
    except BaseException as e:
        print(e)
        return settings.OPERATION_FAILED_MESSAGE.format("convert to jpeg")


def append_images(images, direction='horizontal',
                  bg_color=(255, 255, 255), alignment='centre'):
    """Appends images together

    :param alignment: the alignment of the images. By default set at centre
    :param bg_color: the background colour
    :param images: the input images
    :param direction: the direction which the images are appended together. By default set at "horizontal".
    :return: str with text of image if operation successful. Error message if not.
    """
    try:
        open_images = []
        for image in images:
            open_images.append(Image.open(image))
        widths, heights = zip(*(i.size for i in open_images))

        if direction == 'horizontal':
            new_width = sum(widths)
            new_height = max(heights)
        else:
            new_width = max(widths)
            new_height = sum(heights)

        img = Image.new('RGB', (new_width, new_height), color=bg_color)

        destination_file_name = "appended.png"
        offset = 0
        for im in open_images:
            if direction == 'horizontal':
                y = 0
                if alignment == 'center':
                    y = int((new_height - im.size[1]) / 2)
                elif alignment == 'bottom':
                    y = new_height - im.size[1]
                img.paste(im, (offset, y))
                offset += im.size[0]
            else:
                x = 0
                if alignment == 'center':
                    x = int((new_width - im.size[0]) / 2)
                elif alignment == 'right':
                    x = new_width - im.size[0]
                img.paste(im, (x, offset))
                offset += im.size[1]
        bot_delete_files_in_directory(settings.INPUT_FOLDER)
        img.save(settings.IMAGE_INPUT.format(destination_file_name))
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("append")
    except BaseException as e:
        print(e)
        return settings.OPERATION_SUCCESSFUL_MESSAGE.format("append")


def bot_delete_files_in_directory(path):
    """Deletes all of the files in the given directory

    :param path: str path of directory
    :return: None

    """
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
    """
        Clears notifications
    """
    mastodon.notifications_clear()


def strip_tags(html):
    s = html_stripper.MLStripper()
    s.feed(html)
    return s.get_data()
