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
from nmb.sockets import SocketDispatcher


class Client(SocketDispatcher):
    pass


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
        self.address = ':'.join(map(str, sock))

    def start(self):
        # log dispatcher start request
        logger.debug("Starting dispatcher...")
        # bind to socket
        self.bind(self.sock)
        # listen on socket
        self.listen(5)
        # log dispatcher start
        logger.debug("Dispatcher started.")

    def stop(self):
        # log dispatcher stop request
        logger.debug("Stopping dispatcher...")
        # close socket
        self.close()
        # log dispatcher stop
        logger.debug("Dispatcher stopped.")

    def handle_accept(self):
        # accept connection
        connection = self.accept()
        # return if connection is invalid
        if connection is None:
            return

        # initialize client
        client = Client(connection)
        # log connection
        logger.info("Client [%s] connecting..." % client.address)

        # TODO: handle client transaction
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
        # log server start request
        logger.info("Starting server...")
        # start remote dispatcher
        self.remote.start()
        # log server start
        logger.info("Server started. Awaiting connections at [%s:%s]..." %
            (self.address, self.port))
        # start server loop
        asyncore.loop()
        # stop server
        self.stop()

    def stop(self):
        # log server stop request
        logger.info("Stopping server...")
        # stop remote dispatcher
        self.remote.stop()
        # log server stop
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
    # set file log handler
    logger.setFileLogHandler(args.log)

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
