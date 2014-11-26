#!/usr/bin/env python2

__author__    = "Ryon Sherman"
__email__     = "ryon.sherman@gmail.com"
__copyright__ = "Copyright 2014, Ryon Sherman"
__license__   = "MIT"
__version__   = "1.0"

import os, sys
from setuptools import setup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from nmb import __version__ as VERSION

setup(
    name="nmb",
    version=VERSION,
    author="Ryon Sherman",
    author_email="ryon.sherman@gmail.com",
    url="https://github.com/ryonsherman/network-message-bus",
    description="A TCP network message bus",
    #long_description=open('README.rst').read(),
    packages=['nmb'],
    package_dir={'nmb': 'src/nmb'},
    #install_requires=[],
    entry_points={'console_scripts': [
        'nmb        = nmb:main',
        'nmb-keys   = nmb:nmb_keys',
        'nmb-server = nmb:nmb_server',
        'nmb-client = nmb:nmb_client'
    ]},
    #test_suite="nmb.tests"
)
