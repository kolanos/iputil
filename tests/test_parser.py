import json
import os
import unittest
import uuid

from iputil.parser import find_ips, store_ips

LIST_OF_IPS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'list_of_ips.txt')


class TestFindIPS(unittest.TestCase):
    def test_find_ips(self):
        ips = find_ips(LIST_OF_IPS)
        self.assertEqual(len(ips), 5000)


class TestStoreIPs(unittest.TestCase):
    def setUp(self):
        self.test_cache = '/tmp/%s' % uuid.uuid4().hex
        if os.path.exists(self.test_cache):
            os.unlink(self.test_cache)

    def tearDown(self):
        if os.path.exists(self.test_cache):
            os.unlink(self.test_cache)

    def test_store_ips(self):
        ips = find_ips(LIST_OF_IPS)
        store_ips(self.test_cache, ips)
        with open(self.test_cache) as f:
            stored_ips = json.loads(f.read())
        self.assertEqual(len(stored_ips), 5000)
