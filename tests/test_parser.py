import json
import os
import unittest

from iputil.parser import find_ips, store_ips

TEST_CACHE = '/tmp/.test_cache'
LIST_OF_IPS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'list_of_ips.txt')


class TestFindIPS(unittest.TestCase):
    def test_find_ips(self):
        with open(LIST_OF_IPS) as f:
            ips = find_ips(f.read())
        self.assertEqual(len(ips), 5000)


class TestStoreIPs(unittest.TestCase):
    def test_store_ips(self):
        with open(LIST_OF_IPS) as f:
            ips = find_ips(f.read())
        store_ips(TEST_CACHE, ips)
        with open(TEST_CACHE) as f:
            stored_ips = json.loads(f.read())
        os.unlink(TEST_CACHE)
        self.assertEqual(len(stored_ips), 5000)
