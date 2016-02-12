import json
import os
import re

IP_REGEX = re.compile(r'(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})\.(?:[\d]{1,3})')


def find_ips(filename):
    """Returns all the unique IPs found within a file."""
    matches = []
    with open(filename) as f:
        for line in f:
            matches += IP_REGEX.findall(line)
    return set(sorted(matches)) if matches else set()


def store_ips(cache_path, ips):
    """Stores the IPs into a cache for later retrieval."""
    cache = []
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            cache = json.loads(f.read())
    new_ips = 0
    existing_ips = [i['ip'] for i in cache]
    for ip in ips:
        if ip not in existing_ips:
            cache.append({'ip': ip})
            new_ips += 1
    with open(cache_path, 'wb') as f:
        f.write(json.dumps(cache))
    return new_ips
