#!/usr/bin/env python

import os
import sys

import click

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)

from iputil.filter import ip_filter
from iputil.geoip import geoip_lookup
from iputil.parser import find_ips, store_ips

DEFAULT_CACHE_PATH = '/tmp/.ip_cache'
DEFAULT_MMDB_PATH = os.path.join(PARENT_DIR, 'data', 'GeoLite2-City.mmdb')


@click.group()
@click.option('--cache-path', default=DEFAULT_CACHE_PATH,
              help='Path to cache IP data')
def cli(cache_path):
    global DEFAULT_CACHE_PATH
    DEFAULT_CACHE_PATH = cache_path


@cli.command()
@click.argument('file', type=click.File('rb'))
def parse(file):
    """Parse IPs within a file"""
    ips = find_ips(file.read())
    new_ips = store_ips(DEFAULT_CACHE_PATH, ips)
    click.echo('Found %d IPs, %d of them new.' % (
        len(ips), new_ips))


@cli.command()
@click.option('--mmdb-path', default=DEFAULT_MMDB_PATH,
              help='Path to MaxMind database')
def geoip(mmdb_path):
    """Perform GeoIP lookups"""
    result = geoip_lookup(mmdb_path, DEFAULT_CACHE_PATH)
    if result is None:
        click.echo('Could not read cache or MMDB.')
        exit(1)
    if not result:
        click.echo('Did not find any new GeoIPs')
        exit()
    click.echo('Found new GeoIPs for the following countries:')
    for country, count in result:
        click.echo('%s: %d' % (country, count))


@cli.command()
@click.argument('query')
@click.option('--limit-results', default=100,
              help='Limit number of results')
def filter(query, limit_results):
    """Filters IPs based on query parameters"""
    results = ip_filter(DEFAULT_CACHE_PATH, query)
    if len(results) == 0:
        click.echo('No results found for your query')
        exit()
    click.echo('Found %d IPs matching your query:' % len(results))
    for i, result in enumerate(results):
        if i > limit_results:
            click.echo('...')
            break
        click.echo('%s\t\t%s, %s %s %s' % (
            result['ip'],
            result.get('city', 'N/A'),
            result.get('subdivisions', 'N/A'),
            result.get('postal', 'N/A'),
            result.get('country', 'N/A')))


if __name__ == '__main__':
    cli()
