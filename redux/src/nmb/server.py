#!/usr/bin/env python2

__author__    = "Ryon Sherman"
__email__     = "ryon.sherman@gmail.com"
__copyright__ = "Copyright 2014, Ryon Sherman"
__license__   = "MIT"

import socket
import argparse
import asyncore

from nmb.log import logger
from nmb.parser import parser

TERMINATOR = '\r\n\r\n'

class Client(asyncore.dispatcher_with_send):
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
        logger.debug("Client write(%d) > [%s]: %s" %
            (len(msg), self.address, msg.strip()))

    def read(self):
        # return if buffer has no data
        if not self.buffer: return

        # get buffered data
        data = self.buffer
        # reset data buffer
        self.buffer = ''

    def handle_read(self):
        # receive a chunk of data
        data = self.recv(8192)
        # return if no data received
        if not data: return
        logger.debug("Client read(%d) < [%s]: %s" %
            (len(data), self.address, data.strip()))
        # append data to buffer
        self.buffer += data
        # read buffer if data is terminated
        if data.endswith(TERMINATOR):
            return self.read()

    def handle_close(self):
        logger.info("Client [%s] disconnected." % self.address)
        # close connection
        self.close()

class Dispatcher(asyncore.dispatcher):
    def __init__(self, sock):
        # initialize dispatcher
        asyncore.dispatcher.__init__(self)
        # create socket
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        # reuse address
        self.set_reuse_addr()
        # assign dispatcher properties
        self.sock = sock

    def start(self):
        logger.debug("Starting dispatcher...")
        # bind to socket
        self.bind(self.sock)
        # listen on socket
        self.listen(5)
        logger.debug("Dispatcher started.")

    def stop(self):
        logger.debug("Stopping dispatcher...")
        # close socket
        self.close()
        logger.debug("Dispatcher stopped.")

    def handle_accept(self):
        # accept connection
        connection = self.accept()
        # return if invalid connection
        if connection is None:
            return
        # initialize client
        client = Client(connection)
        logger.info("Client [%s] connecting..." % client.address)
        # TODO:
        client.write('HELO')

class Server(object):
    # default port
    port = 55555
    # default address
    address = '0.0.0.0'

    def __init__(self, **kwargs):
        # assign server properties
        self.port = int(kwargs.get('port', self.port))
        self.address = kwargs.get('address', self.address)

        # initialize remote dispatcher
        self.remote = Dispatcher((self.address, self.port))

    def start(self):
        logger.info("Starting server...")
        # start remote dispatcher
        self.remote.start()
        logger.info("Server started. Awaiting connections at [%s:%s]..." %
            (self.address, self.port))
        # start server loop
        asyncore.loop()
        # stop server
        self.stop()

    def stop(self):
        logger.info("Stopping server...")
        # stop remote dispatcher
        self.remote.stop()
        logger.info("Server stopped.")


def main():
    # define 'dir' argument
    parser.add_argument('--dir', default='./',
        type=parser.path_exists,
        help="Working directory (default: %(default)s)")
    # define 'address' argument
    parser.add_argument('--address', default=Server.address,
        help="Bound interface address (default: %(default)s)")
    # define 'port' argument
    parser.add_argument('--port', type=int, default=Server.port,
        help="Server port (default: %(default)s)")
    # define 'log' argument
    parser.add_argument('--log',
        default='./nmb-server.log',
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

    # initialize server
    server = Server(
        port=args.port,
        address=args.address
    )
    try:
        # run server loop
        server.start()
    except (KeyboardInterrupt, SystemExit):
        # interrupt server loop
        server.stop()

if __name__ == '__main__':
    main()
