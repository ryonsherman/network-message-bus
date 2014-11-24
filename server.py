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


class Dispatcher(asyncore.dispatcher):
    def __init__(self, sock, sock_type):
        asyncore.dispatcher.__init__(self)
        self.sock = sock        
        self.create_socket(sock_type, socket.SOCK_STREAM)

    def listen(self):        
        self.bind(self.sock)
        asyncore.dispatcher.listen(self, 5)

    def stop(self):
        self.close()

    def handle_accept(self):
        connection = self.accept()
        if connection is not None:
            ClientDispatcher(connection)


class RemoteDispatcher(Dispatcher):
    def __init__(self, sock):
        Dispatcher.__init__(self, sock, socket.AF_INET)
        self.set_reuse_addr()

    def connect(self):
        Dispatcher.connect(self, self.sock)


class LocalDispatcher(Dispatcher):
    def __init__(self, sock):
        Dispatcher.__init__(self, sock, socket.AF_UNIX)

    def __unlink_socket(self):
        if os.path.exists(self.sock):
            os.unlink(self.sock)  

    def listen(self):
        self.__unlink_socket()
        Dispatcher.listen(self)

    def stop(self):    
        Dispatcher.stop(self)
        self.__unlink_socket()


class Service(object):
    def __init__(self, remote, local=None):
        self.local  = LocalDispatcher(local or '/tmp/nmb.sock')
        self.remote = RemoteDispatcher(remote)

    def start(self):
        self.local.listen()
        asyncore.loop()

    def stop(self):
        self.local.stop()
        self.remote.stop()


class Server(Service):
    def __init__(self):
        Service.__init__(self, ('0.0.0.0', 55555))

    def start(self):
        self.remote.listen()
        Service.start(self)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    server = Server()
    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        server.stop()
