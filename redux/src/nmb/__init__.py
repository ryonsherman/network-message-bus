#!/usr/bin/env python2

__author__    = "Ryon Sherman"
__email__     = "ryon.sherman@gmail.com"
__copyright__ = "Copyright 2014, Ryon Sherman"
__license__   = "MIT"
__version__   = "1.0"

VERSION = __version__

def nmb_keys():
    pass

def nmb_server():
    from nmb import server
    server.main()

def nmb_client():
    from nmb import client
    client.main()

def main():
    pass

if __name__ == '__main__':
    nmb_server()
