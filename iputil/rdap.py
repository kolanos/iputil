import requests

DEFAULT_RDAP_IP_URL = 'http://rdap.arin.net/registry/ip/{0}'
DEFAULT_RDAP_ENTITY_URL = 'http://rdap.arin.net/registry/entity/{0}'


def lookup(ip):
    r = requests.get(DEFAULT_RDAP_IP_URL.format(ip))
    return r.json()
