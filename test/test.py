from pathlib import Path
from unittest import TestCase

from dotenv import load_dotenv

import bot

load_dotenv()


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
    def test_get_information_about_image_test(self):
        number_of_pixels = 1102500
        expected_x = 700
        expected_y = 525

        expected_string = ("Image properties: "
                           "\n- Number of Pixels: " + "{}"
                           + "\n- Shape/Dimensions: " + "({}, " + "{}, " + "{})").format(number_of_pixels,
                                                                                         expected_y, expected_x, 3)
        result_string = bot.get_information_about_image(str(Path.cwd() /
                                                            "test_resources" / "fibonacciSpiralALOE.jpeg"))
        assert result_string == expected_string

# class TestMastodon(TestCase):
#
#     def test_mastodon_notfications(self):
#         mastodon = Mastodon(
#             access_token=os.getenv("ACCESS_TOKEN"),
#             api_base_url=settings.BASE_ADDRESS
#         )
#         notifications = mastodon.notifications()
#         print(notifications)
