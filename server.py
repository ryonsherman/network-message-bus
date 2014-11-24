#!/usr/bin/env python2

import os
import socket
import asyncore

class ClientDispatcher(asyncore.dispatcher_with_send):
    def __init__(self, (sock, addr)):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.addr = addr

    def handle_read(self):
        data = self.recv(1024)
        if data:
            # TODO: echo for now
            print data,
            self.send(data)


class RemoteDispatcher(asyncore.dispatcher):
    def __init__(self, sock):
        asyncore.dispatcher.__init__(self)        
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.sock = sock

    def start(self):
        self.bind(self.sock)
        self.listen(5)

    def stop(self):
        self.close()

    def handle_accept(self):
        connection = self.accept()
        if connection is not None:
            ClientDispatcher(connection)


class Server(object):
    def __init__(self):
        self.remote = RemoteDispatcher(('127.0.0.1', 55555),)

    def start(self):
        self.remote.start()
        asyncore.loop()

    def stop(self):
        self.remote.stop()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    server = Server()
    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        server.stop()
