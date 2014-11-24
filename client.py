#!/usr/bin/env python2

from server import Service


class Client(Service):
    def __init__(self):
        Service.__init__(self, ('127.0.0.1', 55555), '/tmp/nmb-client.sock')

    def start(self):
        self.remote.connect()
        Service.start(self)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    client = Client()
    try:
        client.start()
    except (KeyboardInterrupt, SystemExit):
        client.stop()
