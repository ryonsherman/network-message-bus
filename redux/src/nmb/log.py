#!/usr/bin/env python2

__author__    = "Ryon Sherman"
__email__     = "ryon.sherman@gmail.com"
__copyright__ = "Copyright 2014, Ryon Sherman"
__license__   = "MIT"

import logging

# def log format
LOG_FORMAT = "[%(asctime)s] (%(levelname)s) %(message)s"

# initialize logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# intitialize log formatter
formatter = logging.Formatter(LOG_FORMAT)

# initialize file log handler
def file_log_handler(log):
    handler = logging.FileHandler(args.log)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
logger.setFileLogHandler = file_log_handler

# initalize console log handler
def console_log_handler(log_level):
    # determine log level if string passed
    if type(log_level) is str:
        log_level = getattr(logging, log_level.upper())
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    logger.addHandler(handler)
logger.setConsoleLogHandler = console_log_handler
