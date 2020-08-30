import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

import cv2
import numpy as np
from dotenv import load_dotenv

import bot

load_dotenv()


def generate_temp_image(temp):
    fibo = str(Path(temp + "/fibo.jpeg"))
    source = str(Path.cwd() / "test_resources" / "fibo.jpeg")
    shutil.copy(source, fibo)
    return fibo


class TestSpamDefender(TestCase):

    def test_add_user_to_requests_test(self):
        spam_defender = bot.SpamDefender()
        assert len(spam_defender.users_who_have_made_requests) == 0
        spam_defender.add_user_to_requests(1)
        assert len(spam_defender.users_who_have_made_requests) == 1
        assert 1 in spam_defender.users_who_have_made_requests

    def test_allow_account_to_make_request(self):
        spam_defender = bot.SpamDefender()
        assert spam_defender.allow_account_to_make_request(1) is True
        spam_defender.add_user_to_requests(1)
        spam_defender.add_user_to_requests(1)
        spam_defender.add_user_to_requests(1)
        spam_defender.add_user_to_requests(1)
        assert spam_defender.allow_account_to_make_request(1) is False


class TestBot(TestCase):
    def test_check_image_type(self):
        return

    def test_get_information_about_image_test(self):
        number_of_pixels = 1102500
        expected_x = 700
        expected_y = 525

        expected_string = ("Image properties: "
                           "\n- Number of Pixels: " + "{}"
                           + "\n- Shape/Dimensions: " + "({}, " + "{}, " + "{})").format(number_of_pixels,
                                                                                         expected_y, expected_x, 3)
        result_string = bot.get_information_about_image(str(Path.cwd() /
                                                            "test_resources" / "fibo.jpeg"))
        assert result_string == expected_string

    def test_get_text_from_images(self):
        expected_text = "This is SAMPLE TEXT\n\n" + "Text is at different regions"
        assert expected_text == bot.get_text_from_image(str(Path.cwd() /
                                                            "test_resources" / "sample_text.jpeg"))

    def test_decolourise_image(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_decolourised_image = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_decolourised.jpeg"))
            bot.decolourise_image(fibo)
            decolourised_image = cv2.imread(fibo)

            assert example_decolourised_image.shape == decolourised_image.shape and not (np.bitwise_xor(
                example_decolourised_image, decolourised_image).any())

    def test_display_colour_channel(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_colour_channel = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_red.jpeg"))
            bot.display_colour_channel(fibo, "red")
            colour_channel = cv2.imread(fibo)

            assert example_colour_channel.shape == colour_channel.shape and not (np.bitwise_xor(
                example_colour_channel, colour_channel).any())

        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_colour_channel = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_blue.jpeg"))
            bot.display_colour_channel(fibo, "blue")
            colour_channel = cv2.imread(fibo)

            assert example_colour_channel.shape == colour_channel.shape and not (np.bitwise_xor(
                example_colour_channel, colour_channel).any())

        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_colour_channel = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_green.jpeg"))
            bot.display_colour_channel(fibo, "green")
            colour_channel = cv2.imread(fibo)

            assert example_colour_channel.shape == colour_channel.shape and not (np.bitwise_xor(
                example_colour_channel, colour_channel).any())

    def test_rotate_image(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_rotation = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_rotate.jpeg"))
            bot.rotate_image(fibo, 75)
            rotated_image = cv2.imread(fibo)

            assert example_rotation.shape == rotated_image.shape and not (np.bitwise_xor(
                example_rotation, rotated_image).any())

    def test_create_border(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_border = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_border.jpeg"))
            bot.create_reflective_border(fibo)
            bordered_image = cv2.imread(fibo)

            assert example_border.shape == bordered_image.shape and not (np.bitwise_xor(
                example_border, bordered_image).any())

    def test_crop_image(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_crop = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_crop.jpeg"))
            bot.crop_image(fibo, "50", "50", "50", "50")
            cropped_image = cv2.imread(fibo)

            assert example_crop.shape == cropped_image.shape and not (np.bitwise_xor(
                example_crop, cropped_image).any())

    def test_enhance_image(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_enhanced = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_enhance.jpeg"))
            bot.enhance_image(fibo)
            enhanced_image = cv2.imread(fibo)

            assert example_enhanced.shape == enhanced_image.shape and not (np.bitwise_xor(
                example_enhanced, enhanced_image).any())

    def test_adjust_brightness(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            # fibo_in = cv2.imread(fibo)
            example_brightness = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_brightness.jpeg"))
            # assert example_brightness.shape == fibo_in.shape and not (np.bitwise_xor(
            #     example_brightness, fibo_in).any())
            bot.adjust_brightness(fibo)
            brighter_image = cv2.imread(fibo)

            assert example_brightness.shape == brighter_image.shape and not (np.bitwise_xor(
                example_brightness, brighter_image).any())

    def test_adjust_colour(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_colour_adjust = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_adjusted_colour.jpeg"))
            bot.adjust_colour(fibo)
            colour_adjusted_image = cv2.imread(fibo)

            assert example_colour_adjust.shape == colour_adjusted_image.shape and not (np.bitwise_xor(
                example_colour_adjust, colour_adjusted_image).any())

    def test_flip_image(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_image_flip = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_flipped.jpeg"))
            bot.flip_image(fibo)
            flipped_image = cv2.imread(fibo)

            assert example_image_flip.shape == flipped_image.shape and not (np.bitwise_xor(
                example_image_flip, flipped_image).any())

    def test_mirror_image(self):
        with TemporaryDirectory() as temp:
            fibo = generate_temp_image(temp)
            example_mirror_image = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_mirrored.jpeg"))
            bot.mirror_image(fibo)
            mirrored_image = cv2.imread(fibo)

            assert example_mirror_image.shape == mirrored_image.shape and not (np.bitwise_xor(
                example_mirror_image, mirrored_image).any())

    # def test_make_transparent_image(self):
    #     with TemporaryDirectory() as temp:
    #         fibo = generate_temp_image(temp)
    #         example_transparent_image = cv2.imread(str(Path.cwd() / "test_resources" / "fibo_transparent.jpeg"))
    #         bot.mirror_image(fibo)
    #         transparent_image = cv2.imread(fibo)
    #
    #         assert example_transparent_image.shape == transparent_image.shape and not (np.bitwise_xor(
    #             example_transparent_image, transparent_image).any())

# class TestMastodon(TestCase):
#
#     def test_mastodon_notfications(self):
#         mastodon = Mastodon(
#             access_token=os.getenv("ACCESS_TOKEN"),
#             api_base_url=settings.BASE_ADDRESS
#         )
#         notifications = mastodon.notifications()
#         print(notifications)
