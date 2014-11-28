#!/usr/bin/env python2

__author__    = "Ryon Sherman"
__email__     = "ryon.sherman@gmail.com"
__copyright__ = "Copyright 2014, Ryon Sherman"
__license__   = "MIT"

import os
import socket
import argparse
import asyncore

from nmb.log import logger
from nmb.parser import parser

TERMINATOR = '\r\n\r\n'


class LocalClient(asyncore.dispatcher_with_send):
    def __init__(self, (sock, addr)):
        # initialize dispatcher
        asyncore.dispatcher_with_send.__init__(self, sock)
        # assign client properties
        self.buffer  = ''
        self.address = ':'.join(map(str, addr))

    def write(self, msg):
        # append terminator if not terminated
        if not msg.endswith(TERMINATOR):
            msg += TERMINATOR
        # send message
        self.send(msg)
        # log write
        logger.debug("Local client write(%d) > [%s]: %s" %
            (len(msg), self.address, msg.strip()))

    def read(self):
        # return if buffer has no data
        if not self.buffer: return

        # get buffered data
        data = self.buffer
        # reset data buffer
        self.buffer = ''

        # TODO: handle read

    def handle_read(self):
        # receive a chunk of data
        data = self.recv(8192)
        # return if no data received
        if not data: return
        # log read
        logger.debug("Local client read(%d) < [%s]: %s" %
            (len(data), self.address, data.strip()))
        # append data to buffer
        self.buffer += data
        # read buffer if data is terminated
        if data.endswith(TERMINATOR):
            return self.read()

    def handle_close(self):
        # log disconnection
        logger.info("Local client [%s] disconnected." % self.address)
        # close connection
        self.close()


class LocalDispatcher(asyncore.dispatcher):
    def __init__(self, sock):
        # initialize dispatcher
        asyncore.dispatcher.__init__(self)
        # create socket
        self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # assign dispatcher properties
        self.sock = sock

    def __unlink_socket(self):
        # unlink socket if exists
        if os.path.exists(self.sock):
            os.unlink(self.sock)

    def start(self):
        # log local dispatcher start request
        logger.debug("Starting local dispatcher...")
        # unlink local socket
        self.__unlink_socket()
        # bind to socket
        self.bind(self.sock)
        # listen on socket
        self.listen(5)
        # log local dispatcher start
        logger.debug("Local dispatcher started.")

    def stop(self):
        # log local dispatcher stop request
        logger.debug("Stopping local dispatcher...")
        # close socket
        self.close()
        # unlink local socket
        self.__unlink_socket()
        # log local dispatcher stop
        logger.debug("Local dispatcher stopped.")

    def handle_accept(self):
        # accept connection
        connection = self.accept()
        # return if connection is invalid
        if connection is None:
            return

        # initialize client
        client = LocalClient(connection)

        # TODO: handle client transaction
        client.write('HELO')


class RemoteDispatcher(asyncore.dispatcher_with_send):
    def __init__(self, sock):
        # initialize dispatcher
        asyncore.dispatcher_with_send.__init__(self)
        # create socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # reuase address
        self.set_reuse_addr()
        # assign dispatcher properties
        self.sock    = sock
        self.buffer  = ''
        self.address = ':'.join(map(str, sock))

    def start(self):
        # log remote dispatcher start request
        logger.debug("Starting remote dispatcher...")
        # connect to socket
        self.connect(self.sock)
        # log remote dispatcher start
        logger.debug("Remote dispatcher started.")

    def stop(self):
        # log remote dispatcher stop request
        logger.debug("Stopping remote dispatcher...")
        # close socket
        self.close()
        # log remote dispatcher stop
        logger.debug("Remote dispatcher stopped.")

    def write(self, msg):
        # append terminator if not terminated
        if not msg.endswith(TERMINATOR):
            msg += TERMINATOR
        # send message
        self.send(msg)
        # log write
        logger.debug("Client write(%d) > [%s]: %s" %
            (len(msg), self.address, msg.strip()))

    def read(self):
        # return if buffer has no data
        if not self.buffer: return

        # get buffered data
        data = self.buffer
        # reset data buffer
        self.buffer = ''

        # TODO: handle read

    def handle_read(self):
        # receive a chunk of data
        data = self.recv(8192)
        # return if no data received
        if not data: return
        # log read
        logger.debug("Client read(%d) < [%s]: %s" %
            (len(data), self.address, data.strip()))
        # append data to buffer
        self.buffer += data
        # read buffer if data is terminated
        if data.endswith(TERMINATOR):
            return self.read()


class Client(object):
    # default port
    port = 55555
    # default address
    address = '127.0.0.1'
    # default local socket
    socket = 'nmb-client.sock'

    def __init__(self, **kwargs):
        # assign client properties
        self.port = int(kwargs.get('port', self.port))
        self.address = kwargs.get('address', self.address)

        # initialize dispatchers
        self.local  = LocalDispatcher(kwargs.get('socket', self.socket))
        self.remote = RemoteDispatcher((self.address, self.port))

    def start(self):
        # log client start request
        logger.info("Starting client...")
        # start local dispatcher
        self.local.start()
        # log local dispatcher start
        logger.info("Awaiting local connections...")
        # start remote dispatcher
        self.remote.start()
        # log client start
        logger.info("Client started. Connecting to [%s:%d]..." % (self.address, self.port))
        # start client loop
        asyncore.loop()
        # stop client
        self.stop()

    def stop(self):
        # log client stop request
        logger.info("Stopping client...")
        # stop local dispatcher
        self.local.stop()
        # stop remote dispatcher
        self.remote.stop()
        # log client stop
        logger.info("Client stopped.")


def main():
    # define 'dir' argument
    parser.add_argument('--dir', default='./',
        type=parser.path_exists,
        help="Working directory (default: %(default)s)")
    # define 'socket' argument
    parser.add_argument('--socket',
        default=Client.socket,
        help="Client local socket (default: %(default)s")
    # define 'address' argument
    parser.add_argument('--address', default=Client.address,
        help="Server address (default: %(default)s)")
    # define 'port' argument
    parser.add_argument('--port', type=int, default=Client.port,
        help="Server port (default: %(default)s)")
    # define 'log' argument
    parser.add_argument('--log',
        default='./nmb-client.log',
        help="Log path (default: %(default)s)")
    # define 'log_level' argument
    parser.add_argument('--log_level', default='INFO',
        choices=['ERROR', 'INFO', 'DEBUG'],
        help="Console log level (default: %(default)s)")
    # define 'silent' argument
    parser.add_argument('--silent', default=False,
        action='store_true',
        help="Disable console log output")
    # parse arguments
    args = parser.parse_args()

    # if console output requested
    if not args.silent:
        # set console log handler
        logger.setConsoleLogHandler(args.log_level)
    # set file log handler
    logger.setFileLogHandler(args.log)

    # initialize client
    client = Client(
        socket=args.socket,
        port=args.port,
        address=args.address
    )
    try:
        # run client loop
        client.start()
    except (KeyboardInterrupt, SystemExit):
        # interrupt client loop
        client.stop()

if __name__ == '__main__':
    main()
