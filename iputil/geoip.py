from collections import defaultdict
import json
import mmap
import operator
import os
import socket
from struct import Struct

MMDB_META_DATA_START = '\xAB\xCD\xEFMaxMind.com'
MMDB_META_DATA_BLOCK_MAX_SIZE = 131072
MMDB_DATA_SECTION_SEPARATOR = 16

unpack_int = Struct('>I').unpack
unpack_long = Struct('>Q').unpack
unpack_short = Struct('>H').unpack


class GeoIP(object):
    """Container for a GEOIP address"""

    __slots__ = ('ip', 'data')

    def __init__(self, ip, data):
        self.ip = ip
        self.data = data

    @property
    def country(self):
        if 'country' in self.data:
            return self.data['country']['iso_code']

    @property
    def country_en(self):
        if 'country' in self.data:
            return self.data['country']['names']['en']

    @property
    def continent(self):
        if 'continent' in self.data:
            return self.data['continent']['code']

    @property
    def state(self):
        return ', '.join([x['iso_code'] for x in self.data.get('subdivisions') or ()
                          if 'iso_code' in x])

    @property
    def postal(self):
        if 'postal' in self.data:
            return self.data['postal'].get('code')

    @property
    def city(self):
        if 'city' in self.data:
            return self.data['city']['names']['en']

    @property
    def timezone(self):
        if 'location' in self.data:
            return self.data['location'].get('time_zone')

    @property
    def location(self):
        if 'location' in self.data:
            lat = self.data['location'].get('latitude')
            long = self.data['location'].get('longitude')
            if lat is not None and long is not None:
                return lat, long

    def to_dict(self):
        return {
            'ip': self.ip,
            'country': self.country,
            'continent': self.continent,
            'state': self.state,
            'city': self.city,
            'postal': self.postal,
            'timezone': self.timezone,
            'location': self.location,
        }


def pack_ip(ip):
    for fmly in socket.AF_INET, socket.AF_INET6:
        try:
            return socket.inet_pton(fmly, ip)
        except socket.error:
            continue
    raise ValueError('Malformed IP address')


class MMDB(object):
    """Context manager to query MaxMind database"""

    def __init__(self, filename, buffer, meta_data):
        self.closed = False
        self.filename = filename
        self.is_ipv6 = meta_data['ip_version'] == 6
        self.nodes = meta_data['node_count']
        self.record_size = meta_data['record_size']
        self.node_size = self.record_size / 4
        self.db_size = self.nodes * self.node_size

        self.buffer = buffer
        self.meta_data = meta_data
        self.reader = MMDBParser(buffer, self.db_size)
        self.ipv4_start = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def close(self):
        self.closed = True
        self.buffer.close()

    def lookup(self, ip_addr):
        if self.closed:
            raise RuntimeError('Database is closed.')
        packed_addr = pack_ip(ip_addr)
        bits = len(packed_addr) * 8
        node = self.find_start_node(bits)
        seen = set()
        for i in xrange(bits):
            if node >= self.nodes:
                break
            bit = (ord(packed_addr[i >> 3]) >> (7 - (i % 8))) & 1
            node = self.parse_node(node, bit)
            if node in seen:
                raise LookupError('Circle in tree detected')
            seen.add(node)
        if node > self.nodes:
            offset = node - self.nodes + self.db_size
            return GeoIP(ip_addr, self.reader.read(offset)[0])

    def find_start_node(self, bits):
        if bits == 128 or not self.is_ipv6:
            return 0
        if self.ipv4_start is not None:
            return self.ipv4_start
        node = 0
        for netmask in xrange(96):
            if node >= self.nodes:
                break
            node = self.parse_node(netmask, 0)
        self.ipv4_start = node
        return node

    def parse_node(self, node, index):
        offset = node * self.node_size
        if self.record_size == 24:
            offset += index * 3
            bytes = '\x00' + self.buffer[offset:offset + 3]
        elif self.record_size == 28:
            b = ord(self.buffer[offset + 3:offset + 4])
            if index:
                b &= 0x0F
            else:
                b = (0xF0 & b) >> 4
            offset += index * 4
            bytes = chr(b) + self.buffer[offset:offset + 3]
        elif self.record_size == 32:
            offset += index * 4
            bytes = self.buffer[offset:offset + 4]
        else:
            raise LookupError('Invalid record size')
        return unpack_int(bytes)[0]


def make_struct_parser(code):
    """Helper to create struct unpack methods."""
    struct = Struct('>' + code)

    def unpack_func(self, size, offset):
        new_offset = offset + struct.size
        bytes = self.buffer[offset:new_offset].rjust(struct.size, '\x00')
        value = struct.unpack(bytes)[0]
        return value, new_offset
    return unpack_func


class MMDBParser(object):
    """
    Parser for MaxMind MMDB binary format.

    Reference: https://maxmind.github.io/MaxMind-DB/
    """

    def __init__(self, buffer, offset=0):
        self.buffer = buffer
        self.offset = offset

    def parse_ptr(self, size, offset):
        ptr_size = ((size >> 3) & 0x3) + 1
        bytes = self.buffer[offset:offset + ptr_size]
        if ptr_size != 4:
            bytes = chr(size & 0x7) + bytes
        ptr = (
            unpack_int(bytes.rjust(4, '\x00'))[0] +
            self.offset +
            MMDB_DATA_SECTION_SEPARATOR +
            (0, 2048, 526336, 0)[ptr_size - 1]
        )
        return self.read(ptr)[0], offset + ptr_size

    def parse_str(self, size, offset):
        bytes = self.buffer[offset:offset + size]
        return bytes.decode('utf-8', 'replace'), offset + size

    parse_double = make_struct_parser('d')

    def parse_bytes(self, size, offset):
        return self.buffer[offset:offset + size], offset + size

    def parse_uint(self, size, offset):
        bytes = self.buffer[offset:offset + size]
        return unpack_long(bytes.rjust(8, '\x00'))[0], offset + size

    def parse_dict(self, size, offset):
        container = {}
        for _ in xrange(size):
            key, offset = self.read(offset)
            value, offset = self.read(offset)
            container[key] = value
        return container, offset

    parse_int32 = make_struct_parser('i')

    def parse_list(self, size, offset):
        rv = [None] * size
        for idx in xrange(size):
            rv[idx], offset = self.read(offset)
        return rv, offset

    def parse_error(self, size, offset):
        raise AssertionError('Read invalid type code')

    def parse_bool(self, size, offset):
        return size != 0, offset

    parse_float = make_struct_parser('f')

    callbacks = (
        parse_error,
        parse_ptr,
        parse_str,
        parse_double,
        parse_bytes,
        parse_uint,
        parse_uint,
        parse_dict,
        parse_int32,
        parse_uint,
        parse_uint,
        parse_list,
        parse_error,
        parse_error,
        parse_bool,
        parse_float,
    )

    def read(self, offset):
        new_offset = offset + 1
        byte = ord(self.buffer[offset:new_offset])
        size = byte & 0x1f
        ty = byte >> 5
        if ty == 0:
            byte = ord(self.buffer[new_offset:new_offset + 1])
            ty = byte + 7
            new_offset += 1
        if ty != 1 and size >= 29:
            to_read = size - 28
            bytes = self.buffer[new_offset:new_offset + to_read]
            new_offset += to_read
            if size == 29:
                size = 29 + ord(bytes)
            elif size == 30:
                size = 285 + unpack_short(bytes)[0]
            elif size > 30:
                size = 65821 + unpack_int(bytes.rjust(4, '\x00'))[0]
        return self.callbacks[ty](self, size, new_offset)


def read_mmdb_meta_data(buffer):
    offset = buffer.rfind(MMDB_META_DATA_START,
                          buffer.size() - MMDB_META_DATA_BLOCK_MAX_SIZE)
    if offset < 0:
        raise ValueError('Could not find meta data')
    offset += len(MMDB_META_DATA_START)
    return MMDBParser(buffer, offset).read(offset)[0]


def open_mmdb(filename):
    """Open memory mapped buffer of MMDB"""
    with open(filename, 'rb') as f:
        mmap_buffer = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    meta_data = read_mmdb_meta_data(mmap_buffer)
    return MMDB(filename, mmap_buffer, meta_data)


def geoip_lookup(mmdb_path, cache_path):
    """Performs GeoIP lookups for IPs stored in cache"""
    if not os.path.exists(cache_path):
        return None
    with open(cache_path, 'rb') as f:
        cache = json.loads(f.read())
    result = defaultdict(lambda: 0)
    with open_mmdb(mmdb_path) as db:
        for i, ip_data in enumerate(cache):
            if 'geoip' not in ip_data:
                geoip = db.lookup(ip_data['ip'])
                if geoip:
                    cache[i].update(geoip=True, **geoip.to_dict())
                    result[geoip.country_en] += 1
    with open(cache_path, 'wb') as f:
        f.write(json.dumps(cache))
    return sorted(result.items(), key=operator.itemgetter(1), reverse=True)
