from unittest import TestCase


class TestSpamDefender(TestCase):
    def test_allow_account_to_make_request(self):
        self.assertTrue(1 == 1)
        self.assertFalse(1 == 2)



