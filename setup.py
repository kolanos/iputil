#!/usr/bin/env python

from setuptools import setup, find_packages

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]

setup(
   name='iputil',
   version='0.1.0',
   author='Michael Lavers',
   author_email='kolanos@gmail.com',
   url='https://www.github.com/kolanos/iputil',
   description='A utility to parse IPs from text and filter them.',
   packages=find_packages(),
   include_package_data=True,
   package_data={'': ['*.txt', '*.rst', '*.json']},
   scripts=['bin/iputil'],
   keywords='python tools utils',
   license='MIT',
   install_requires=REQUIREMENTS,
)
