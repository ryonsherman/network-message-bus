#!/usr/bin/env python2

__author__    = "Ryon Sherman"
__email__     = "ryon.sherman@gmail.com"
__copyright__ = "Copyright 2014, Ryon Sherman"
__license__   = "MIT"

import os
import argparse

# initialize argument parser
parser = argparse.ArgumentParser()

# define 'path_exists' argument type
def path_exists(path):
    if not os.path.exists(path):
        error = "No such file or directory: '%s'" % path
        raise argparse.ArgumentTypeError(error)
    return path
parser.path_exists = path_exists
