import unittest
from time import sleep
try:
    import mock
except ImportError:
    from unittest import mock
import socket
import rswarp.utilities.server.parser as parser
import rswarp.utilities.server.scan_rsmpi as rsmpiServer
import sys
from contextlib import contextmanager
from StringIO import StringIO


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestParser(unittest.TestCase):
    @mock.patch('sys.argv', ['', 'server', '--add', '1'])
    def test_parser_server_start(self):
        # with mock.patch('sys.argv', ['', 'server', '--add', '1']):
        my_parser = parser.ParserSetup()
        parsed = my_parser()
        self.assertEqual(parsed.id, 1)
        self.assertEqual(parsed.server_action, 'add_server')

    @mock.patch('sys.argv', ['', 'server', '--remove', '1'])
    def test_parser_server_remove(self):
        # with mock.patch('sys.argv', ['', 'server', '--add', '1']):
        my_parser = parser.ParserSetup()
        parsed = my_parser()
        self.assertEqual(parsed.id, 1)
        self.assertEqual(parsed.server_action, 'remove_server')

    @mock.patch('sys.argv', ['', 'server', '--stop', '1'])
    def test_parser_server_stop(self):
        # with mock.patch('sys.argv', ['', 'server', '--add', '1']):
        my_parser = parser.ParserSetup()
        parsed = my_parser()
        self.assertEqual(parsed.id, 1)
        self.assertEqual(parsed.server_action, 'stop_server')


class TestServerBasics(unittest.TestCase):

    def test_signal_receive(self):
        server = rsmpiServer.JobServer()
        s = socket.socket()
        HOST = '127.0.0.1'
        PORT = 10000
        s.connect((HOST, PORT))
        with captured_output() as (out, err):
            s.send('hii')
            sleep(0.001)
            self.assertEqual(out.getvalue().strip(), 'Buffer received: hii')
        # server.__exit__()


if __name__ == '__main__':
    unittest.main()