#!/usr/bin/env python2

import os
import stat
import socket
import base64
import logging
import asyncore

terminator = '\r\n\r\n'
logger = logging.getLogger()


class ClientDispatcher(asyncore.dispatcher_with_send):
    def __init__(self, server, (sock, addr)):
        asyncore.dispatcher_with_send.__init__(self, sock)

        self.server = server
        self.address = ':'.join(map(str, addr))

        self.gpg   = False
        self.data  = ''
        self.state = 'NOAUTH'
        self.connected = False

    def write(self, msg, enc=False):
        if enc and self.gpg and self.server.gpg.target:
            msg = self.server.gpg.encrypt(msg,
                self.server.gpg.target)
            msg = base64.b64encode(str(msg))
        if not msg.endswith(terminator):
            msg += terminator
        self.send(msg)
        logger.debug("Client write(%d) > [%s]: %s" %
            (len(msg), self.address, msg.strip()))

    def read(self):
        if not self.data:
            return

        data = self.data
        self.data = ''

        if self.gpg and self.server.gpg.target:
            data = base64.b64decode(data)
            data = str(self.server.gpg.decrypt(data))

        data = data.strip().split(':')
        if data[0] == 'SYNACK' and self.state == 'NOAUTH':
            cmd = data[0]
            if len(data) > 1:
                cmd += '(PUBKEY)'
                if not self.server.gpg:
                    logging.error("GPG not enabled; disconnecting")
                    self.close()
                    return
                self.gpg = True
                pubkey = base64.b64decode(data[1])
                pubkey = self.server.gpg.import_keys(pubkey)
                if not len(pubkey.results):
                    logging.error("Failed to receive GPG key; disconnecting")
                    return self.close()
                self.server.gpg.target = pubkey.results[0]['fingerprint']
            logging.debug("2) %s received" % cmd)
            self.state = 'ACK'
            raw = cmd = self.state
            if self.server.gpg:
                cmd += '(PUBKEY)'
                pubkey = self.server.gpg.pubkey
                pubkey = self.server.gpg.export_keys(pubkey)
                raw += ':%s' % base64.b64encode(pubkey)
            self.write(raw)
            logging.debug("3) Sending %s" % cmd)
            self.state = 'AUTH'
            self.connected = True
            logging.info("Client [%s] connected." % self.address)
            logging.info("Authenticating client [%s]..." % self.address)
        elif data[0] == 'AUTH' and self.state == 'AUTH':
            cmd = 'AUTH:%s' % self.server.gpg.target
            self.write(cmd, True)
            logging.info("Client authenticated.")

    def handle_read(self):
        data = self.recv(8192)
        if not data:
            return
        logger.debug("Client read(%d) < [%s]: %s" %
            (len(data), self.address, data.strip()))
        self.data += data
        if data.endswith(terminator):
            return self.read()

    def handle_close(self):
        logger.info("Client [%s] disconnected." % self.address)
        self.close()


class Dispatcher(asyncore.dispatcher):
    def __init__(self, server, sock):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()

        self.server = server
        self.sock = sock

    def start(self):
        logging.debug("Starting dispatcher...")
        self.bind(self.sock)
        self.listen(5)
        logging.debug("Dispatcher started.")

    def stop(self):
        logging.debug("Stopping dispatcher...")
        self.close()
        logging.debug("Dispatcher stopped.")

    def handle_accept(self):
        connection = self.accept()
        if connection is not None:
            client = ClientDispatcher(self.server, connection)
            logger.info("Client [%s] connecting..." % client.address)
            client.write('SYN:AUTH' if self.server.gpg else 'SYN')
            logger.debug('1) SYN sent; expecting SYNACK')


class Server(object):
    port = 55555
    address = '0.0.0.0'

    def __init__(self, **kwargs):
        self.gpg  = kwargs.get('gpg', None)
        self.port = int(kwargs.get('port', self.port))
        self.address = kwargs.get('address', self.address)
        self.remote  = Dispatcher(self, (self.address, self.port))

    def start(self):
        logging.info("Starting server...")
        self.remote.start()
        logging.info("Server started. Awaiting connections at [%s:%s]..." % (self.address, self.port))
        asyncore.loop()

    def stop(self):
        logging.info("Stopping server...")
        self.remote.stop()
        logging.info("Server stopped.")


if __name__ == '__main__':
    working_dir = '/var/run/nmb'

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir',
        default=working_dir,
        help="Working directory (default: %(default)s)")
    parser.add_argument('--address',
        default=Server.address,
        help="Bound interface address (default: %(default)s)")
    parser.add_argument('--port',
        default=Server.port, type=int,
        help="Server port (default: %(default)s)")
    parser.add_argument('--gpg',
        default=False, action='store_true',
        help="Use GPG encryption")
    parser.add_argument('--log',
        default=os.path.join(working_dir, 'nmb-server.log'),
        help="Log path (default: %(default)s")
    parser.add_argument('--log_level',
        default='INFO',
        help="Console log level (default: %(default)s")
    parser.add_argument('--silent',
        action='store_true', default=False,
        help="Disable console log output")
    args = parser.parse_args()

    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    log_level = getattr(logging, args.log_level.upper())
    log_format = "[%(asctime)s] (%(levelname)s) %(message)s"

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(log_format)
    if not args.silent:
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    handler = logging.FileHandler(args.log)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    if args.gpg:
        import gnupg
        gpghome = os.path.join(args.dir, 'gpg')
        if not os.path.exists(gpghome):
            os.makedirs(gpghome)
            os.chmod(gpghome, 0700)
        gpg = gnupg.GPG(gnupghome=gpghome)
        if not gpg.list_keys(True):
            gpg.gen_key(gpg.gen_key_input())
        gpg.pubkey = gpg.list_keys(True)[0]['fingerprint']
        gpg.target = None

    server = Server(
        dir=args.dir,
        port=args.port,
        address=args.address,
        gpg=gpg if args.gpg else False
    )
    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        server.stop()
