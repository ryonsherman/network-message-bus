#!/usr/bin/env python2

import os
import socket
import asyncore

# import random
# import hashlib
# def foo():
#     return hashlib.sha224(str(random.getrandbits(256))).hexdigest();

class ClientDispatcher(asyncore.dispatcher_with_send):
    def __init__(self, (sock, addr)):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.addr = addr

    def handle_read(self):
        data = self.recv(1024)
        if data:
            # TODO: echo for now
            print data,


class LocalDispatcher(asyncore.dispatcher):
    def __init__(self, sock=None):
        asyncore.dispatcher.__init__(self)        
        self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock = sock

    def __unlink_socket(self):
        if os.path.exists(self.sock):
            os.unlink(self.sock)  

    def start(self):
        self.__unlink_socket()
        self.bind(self.sock)
        self.listen(5)

    def stop(self):
        self.close()
        self.__unlink_socket()

    def handle_accept(self):
        connection = self.accept()
        if connection is not None:
            ClientDispatcher(connection)


class RemoteDispatcher(asyncore.dispatcher_with_send):
    def __init__(self, sock):
        asyncore.dispatcher_with_send.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.sock = sock
        # self.step = 'AUTH'
        # self.connected = False

    def start(self):
        self.connect(self.sock)
        # self.write(self.step)

    def stop(self):
        self.close()

    def write(self, msg):
        if not msg.endswith('\n'):
            msg += '\n'
        self.send(msg)
        print 'write: %s' % msg.strip()

    def handle_read(self):
        raw = self.recv(8192)
        if not raw:
            return

        # data = raw.strip().split(':')
        data = raw.strip()
        print 'read: %s' % data

        # if data[0] == 'SYN' and self.step == 'AUTH':
        #     self.step = 'SYNACK'
        #     # self.write('%s:PUBKEY' % self.step)
        #     self.write(self.step)
        # elif data[0] == 'ACK' and self.step == 'SYNACK':
        #     self.step = 'FIN'
        #     # self.write('%s:APIKEY' % self.step)
        #     self.write(self.step)
        # elif data[0] == 'FIN' and self.step == 'FIN':
        #     self.connected = True


class Client(object):
    def __init__(self):
        self.local  = LocalDispatcher('/tmp/nbm.sock')
        self.remote = RemoteDispatcher(('127.0.0.1', 55555),)

    def start(self):
        self.local.start()
        self.remote.start()
        asyncore.loop()

    def stop(self):
        self.local.stop()
        self.remote.stop()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    
    client = Client()
    try:
        client.start()
    except (KeyboardInterrupt, SystemExit):
        client.stop()
