#!/usr/bin/env python2

__author__    = "Ryon Sherman"
__email__     = "ryon.sherman@gmail.com"
__copyright__ = "Copyright 2014, Ryon Sherman"
__license__   = "MIT"

import asyncore

from nmb.log import logger

CHUNK_SIZE = 8192
TERMINATOR = '\r\n\r\n'

class SocketDispatcher(asyncore.dispatcher_with_send):
    def __init__(self, (sock, addr)):
        # initialize dispatcher
        asyncore.dispatcher_with_send.__init__(self, sock)
        # assign socket properties
        self.buffer  = ''
        self.address = ':'.join(map(str, addr))

    def write(self, data):
        # append terminator if not terminated
        if not data.endswith(TERMINATOR):
            data += TERMINATOR
        # send message
        self.send(data)

        # log write
        logger.debug("%s write(%d) > [%s]: %s" % (
            self.__class__.__name__,
            len(data), self.address, data.strip()))

    def read(self):
        # return if buffer has no data
        if not self.buffer: return

        # get buffered data
        data = self.buffer
        # reset data buffer
        self.buffer = ''

        # returned buffered data
        return data

    def handle_read(self):
        # receive a chunk of data
        data = self.recv(CHUNK_SIZE)
        # return if no data received
        if not data: return

        # log read
        logger.debug("%s read(%d) < [%s]: %s" % (
            self.__class__.__name__,
            len(data), self.address, data.strip()))

        # append data to buffer
        self.buffer += data
        # read buffer if data is terminated
        if data.endswith(TERMINATOR):
            return self.read()

    def handle_close(self):
        # log disconnection
        logger.info("%s [%s] disconnected." % (
            self.__class__.__name__, self.address))

        # close connection
        self.close()
