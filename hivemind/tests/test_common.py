import unittest

from hivemind import common


class CommonTestCase(unittest.TestCase):
    def test_list_commands(self):
        common.list_commands()

    def test_load_fabfile(self):
        common._load_fabfile()
