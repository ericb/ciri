#!/usr/bin/env python
import codecs
import os
import re
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='ciri',
    version=find_version('ciri', '__init__.py'),
    description='Python Schema Library',
    url='https://github.com/ericb/ciri',
    author='Eric Bobbitt <eric@hellosuer.net>, Daniel Imhoff <dwieeb@gmail.com>',
    author_email='eric@hellouser.net'
    packages=find_packages(exclude=('test*', 'docs*')),
    package_dir={'ciri': 'ciri'},
    include_package_data=True,
    license='MIT'
)
