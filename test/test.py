from unittest import TestCase

import bot


class TestSpamDefender(TestCase):

    def test_add_user_to_requests(self):
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
