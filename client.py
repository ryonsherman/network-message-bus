#!/usr/bin/env python2

import os
import stat
import socket
import base64
import logging
import asyncore

terminator = '\r\n\r\n'
logger = logging.getLogger()

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
        logging.debug("Starting local dispatcher...")
        self.__unlink_socket()
        self.bind(self.sock)
        self.listen(5)
        logging.debug("Local dispatcher started.")

    def stop(self):
        logging.debug("Stopping local dispatcher...")
        self.close()
        self.__unlink_socket()
        logging.debug("Local dispatcher stopped.")

    def handle_accept(self):
        connection = self.accept()
        if connection is not None:
            ClientDispatcher(connection)


class RemoteDispatcher(asyncore.dispatcher_with_send):
    def __init__(self, client, sock):
        asyncore.dispatcher_with_send.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()

        self.client = client
        self.sock = sock
        self.address = ':'.join(map(str, sock))

        self.gpg   = False
        self.data  = ''
        self.state = 'NOAUTH'
        self.connected = False

    def start(self):
        logging.debug("Starting remote dispatcher...")
        self.connect(self.sock)
        logging.debug("Remote dispatcher started.")

    def stop(self):
        logging.debug("Stopping remote dispatcher...")
        self.close()
        logging.debug("Remote dispatcher stopped.")

    def write(self, msg, enc=False):
        if enc and self.gpg and self.client.gpg.target:
            msg = self.client.gpg.encrypt(msg,
                self.client.gpg.target)
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

        if self.gpg and self.client.gpg.target:
            data = base64.b64decode(data)
            data = str(self.client.gpg.decrypt(data))

        data = data.strip().split(':')
        if data[0] == 'SYN' and self.state == 'NOAUTH':
            cmd = data[0]
            if len(data) > 1 and data[1] == 'AUTH':
                cmd += '(%s)' % data[1]
                if not self.client.gpg:
                    logging.error("GPG required")
                    self.client.stop()
                    return
                self.gpg = True
            logging.debug("1) %s received; sending SYNACK" % cmd)
            self.state = 'SYNACK'
            raw = cmd = self.state
            if self.gpg:
                cmd += '(PUBKEY)'
                pubkey = self.client.gpg.pubkey
                pubkey = self.client.gpg.export_keys(pubkey)
                raw += ':%s' % base64.b64encode(pubkey)
            self.write(raw)
            logging.debug("2) Sent %s; expecting ACK" % cmd)
        elif data[0] == 'ACK' and self.state == 'SYNACK':
            cmd = data[0]
            if len(data) > 1:
                cmd += '(PUBKEY)'
                if not self.gpg:
                    logging.error("GPG not enabled.")
                    return self.close()
                pubkey = base64.b64decode(data[1])
                pubkey = self.client.gpg.import_keys(pubkey)
                if not len(pubkey.results):
                    logging.error("Failed to receive GPG key".)
                    return self.close()
                self.client.gpg.target = pubkey.results[0]['fingerprint']
            logging.debug("3) %s received" % cmd)
            self.state = 'AUTH'
            self.connected = True
            logging.info("Connected to server.")

            if self.gpg:
                key = self.client.gpg.pubkey
            else:
                key = '12345'
                # TODO: determine non-gpg unique id
            cmd = 'AUTH:%s' % key
            self.write(cmd, True)
            logging.info("Authenticating with server...")
        elif data[0] == 'AUTH' and self.state == 'AUTH':
            if len(data) < 2 or data[1] != self.client.gpg.pubkey:
                logging.error("Server rejected authentication.")
                return self.close()
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

class Client(object):
    port = 55555
    address = '127.0.0.1'
    socket = '/tmp/nmb-client.sock'

    def __init__(self, **kwargs):
        self.gpg     = kwargs.get('gpg', None)
        self.port    = int(kwargs.get('port', self.port))
        self.address = kwargs.get('address', self.address)
        self.remote = RemoteDispatcher(self, (self.address, self.port))
        self.local  = LocalDispatcher(kwargs.get('socket', self.socket))

    def start(self):
        logging.info("Starting client...")
        self.local.start()
        logging.info("Awaiting local connections...")
        self.remote.start()
        logging.info("Client started. Connecting to [%s:%d]..." % (self.address, self.port))
        asyncore.loop()

    def stop(self):
        logging.info("Stopping client...")
        self.local.stop()
        self.remote.stop()
        logging.info("Client stopped.")


if __name__ == '__main__':
    working_dir = '/var/run/nmb'

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir',
        default=working_dir,
        help="Working directory (default: %(default)s)")
    parser.add_argument('--socket',
        default=Client.socket,
        help="Client local socket (default: %(default)s")
    parser.add_argument('--address',
        default=Client.address,
        help="Server address (default: %(default)s)")
    parser.add_argument('--port',
        default=Client.port, type=int,
        help="Server port (default: %(default)s)")
    parser.add_argument('--gpg',
        default=False, action='store_true',
        help="Use GPG encryption")
    parser.add_argument('--log',
        default=os.path.join(working_dir, 'nmb-client.log'),
        help="Log path (default: %(default)s")
    parser.add_argument('--log_level',
        default='INFO',
        help="Console log level (default: %(default)s")
    parser.add_argument('--silent',
        action='store_true', default=False,
        help="Disable console log output")
    args = parser.parse_args()

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

    client = Client(
        dir=args.dir,
        port=args.port,
        address=args.address,
        gpg=gpg if args.gpg else False,
        sock=os.path.join(args.dir, 'nmb-client.sock')
    )
    try:
        client.start()
    except (KeyboardInterrupt, SystemExit):
        client.stop()
