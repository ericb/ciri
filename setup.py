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
    long_description=read('README.rst'),
    keywords='schema serialization deserialization serialize deserialize encode decode validation validate rest api',
    url='https://github.com/ericb/ciri',
    project_urls={
        'Documentation': 'https://ciri.hellouser.net',
        'Source': 'https://github.com/ericb/ciri',
        'Tracker': 'https://github.com/ericb/ciri/issues',
    },
    author='Eric Bobbitt',
    author_email='eric@hellouser.net',
    packages=find_packages(exclude=('test*', 'docs')),
    package_dir={'ciri': 'ciri'},
    include_package_data=True,
    python_requires='>=2.6',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities'
    ]
)
