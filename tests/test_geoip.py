import os
import unittest
import uuid

from iputil.geoip import geoip_lookup, open_mmdb
from iputil.parser import find_ips, store_ips

LIST_OF_IPS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'list_of_ips.txt')
MMDB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'GeoLite2-City.mmdb')


class TestOpenMMDB(unittest.TestCase):
    def test_open_mmdb(self):
        with open_mmdb(MMDB) as db:
            ip = db.lookup('8.8.8.8')
        self.assertEqual(ip.country, 'US')
        self.assertEqual(ip.state, 'CA')
        self.assertEqual(ip.city, 'Mountain View')


class TestGeoIPLookup(unittest.TestCase):
    def setUp(self):
        self.test_cache = '/tmp/%s' % uuid.uuid4().hex
        if os.path.exists(self.test_cache):
            os.unlink(self.test_cache)

    def tearDown(self):
        if os.path.exists(self.test_cache):
            os.unlink(self.test_cache)

    def test_geoip_lookup(self):
        ips = find_ips(LIST_OF_IPS)
        store_ips(self.test_cache, ips)
        result = geoip_lookup(MMDB, self.test_cache)
        self.assertEqual(len(result), 113)
