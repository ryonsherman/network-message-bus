#!/usr/bin/env python2

import os
import socket
import asyncore


class ClientDispatcher(asyncore.dispatcher_with_send):
    def __init__(self, (sock, addr)):
        asyncore.dispatcher_with_send.__init__(self, sock)
        self.addr = ':'.join(map(str, addr))
        # self.step = 'NOAUTH'
        # self.connected = False

    def write(self, msg):
        if not msg.endswith('\n'):
            msg += '\n'
        self.send(msg)
        print 'write(%s):' % self.addr, msg.strip()

    def handle_read(self):
        raw = self.recv(8192)
        if not raw:
            return

        # data = raw.strip().split(':')
        data = raw.strip()
        print 'read(%s):' % self.addr, data

        # if data[0] == 'AUTH' and self.step == 'NOAUTH':
        #     self.step = 'SYN'
        #     # self.write('%s:PUBKEY' % self.step)
        #     self.write(self.step)
        # elif data[0] == 'SYNACK' and self.step == 'SYN':
        #     self.step = 'ACK'
        #     # self.write('%s:APIKEY' % self.step)
        #     self.write(self.step)
        # elif data[0] == 'FIN' and self.step == 'ACK':
        #     self.step = 'FIN'
        #     self.write(self.step)
        #     self.connected = True

        #     print 'auth(%s)' % self.addr
        # elif self.connected:
        #     self.write('ERROR')
        # else:
        #     self.write('NOAUTH')

    def handle_close(self):
        print 'disconnect(%s)' % self.addr
        self.close()


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
            client = ClientDispatcher(connection)
            print 'connect(%s)' % client.addr

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
