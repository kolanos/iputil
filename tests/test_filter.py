import os
import uuid
import unittest

from iputil.filter import filter_ips
from iputil.geoip import geoip_lookup
from iputil.parser import find_ips, store_ips

LIST_OF_IPS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'list_of_ips.txt')
MMDB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'GeoLite2-City.mmdb')



class TestFilterIPs(unittest.TestCase):
    def setUp(self):
        self.test_cache = '/tmp/%s' % uuid.uuid4().hex
        if os.path.exists(self.test_cache):
            os.unlink(self.test_cache)

    def tearDown(self):
        if os.path.exists(self.test_cache):
            os.unlink(self.test_cache)

    def test_filter_ips(self):
        with open(LIST_OF_IPS) as f:
            ips = find_ips(f.read())
        store_ips(self.test_cache, ips)
        geoip_lookup(MMDB, self.test_cache)

        result = filter_ips(self.test_cache, 'country == US')
        self.assertEqual(len(result), 1856)
