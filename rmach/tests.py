import copy
import unittest
import urllib
import logging
import datetime
import random
import string
import urlparse

from nose.tools import assert_equals, assert_raises, assert_true, assert_false

from rapidsms.router import Router
from rapidsms.messages.incoming import IncomingMessage
from rapidsms.models import Connection, Contact, Backend
from rapidsms.messages.outgoing import OutgoingMessage

from rmach.backend import MachBackend, MachImproperlyConfigured


logging.basicConfig(level=logging.DEBUG)

basic_conf = {
    'config': {
        'id': 'XXXX',
        'password': 'YYYYYYYY',
        'number': '(###) ###-####',
    }
}


class MockRouter(Router):
    def start(self):
        self.running = True
        self.accepting = True
        self._start_all_backends()
        self._start_all_apps()

    def stop(self):
        self.running = False
        self.accepting = False
        self._stop_all_backends()


UNICODE_CHARS = [unichr(x) for x in xrange(1, 0xD7FF)]

def random_unicode_string(max_length=255):
    output = u''
    for x in xrange(random.randint(1, max_length/2)):
        c = UNICODE_CHARS[random.randint(0, len(UNICODE_CHARS)-1)]
        output += c + u' '
    return output


def get_random_string(length=50, choices=string.ascii_letters):
    return u''.join(random.choice(choices) for x in xrange(length))
    

def test_good_message():
    """ Make sure backend creates IncomingMessage properly """
    backend = MachBackend(name="mach", router=None, **basic_conf)
    data = {'snr': '1112229999', 'msg': 'Hi'}
    message = backend.message(data)
    assert_true(isinstance(message, IncomingMessage))
    assert_true(isinstance(message.connection, Connection))
    assert_equals(message.connection.identity, data['snr'])
    assert_equals(message.text, data['msg'])
    

def test_bad_message():
    """ Don't die if POSTed data doesn't contain the necessary items """
    backend = MachBackend(name="mach", router=None, **basic_conf)
    data = {'foo': 'moo'}
    message = backend.message(data)
    assert_equals(message, None)


def test_backend_route():
    router = MockRouter()
    backend = MachBackend(name="mach", router=router, **basic_conf)
    router.start()
    Connection.objects.all().delete()
    conn = Connection.objects.create(backend=backend.model,
                                     identity='1112229999')
    message = IncomingMessage(conn, 'Hi', datetime.datetime.now())
    assert_true(backend.route(message), True)


def test_outgoing_unicode_characters():
    """ Outgoing unicode characters need to be UCS/UTF-16 encoded """
    backend = MachBackend(name="mach", router=None, **basic_conf)
    bk = Backend.objects.create(name='test')
    connection = Connection.objects.create(identity='1112229999', backend=bk)
    text = random_unicode_string(20)
    message = OutgoingMessage(connection, text)
    data = backend.prepare_message(message)
    assert_equals(data['msg'].decode(MachBackend.encoding), text)
    assert_true(data['encoding'], 'ucs')


def test_incoming_unicode_characters():
    backend = MachBackend(name="mach", router=None, **basic_conf)
    text = random_unicode_string(20)
    data = {'snr': '1112229999', 'msg': text}
    message = backend.message(data)
    assert_equals(text, message.text)


def test_required_config_parameters():
    """ id, password, and number are required in the backend config. """
    for key in ['id', 'password', 'number']:
        config = copy.deepcopy(basic_conf)
        del config['config'][key]
        assert_raises(MachImproperlyConfigured, MachBackend, name="mach", router=None, **config)


def test_long_ascii_message():
    """ ASCII messages over 160 characters should have a split parameter """
    backend = MachBackend(name="mach", router=None, **basic_conf)
    bk = Backend.objects.create(name='long-ascii')
    connection = Connection.objects.create(identity='1112229999', backend=bk)
    text = get_random_string(200)
    message = OutgoingMessage(connection, text)
    data = backend.prepare_message(message)
    assert_equals(data['split'], 2)


def test_long_unicode_message():
    """ Unicode messages over 70 characters should have a split parameter """
    backend = MachBackend(name="mach", router=None, **basic_conf)
    bk = Backend.objects.create(name='long-unicode')
    connection = Connection.objects.create(identity='1112229999', backend=bk)
    text = get_random_string(200, choices=UNICODE_CHARS)
    message = OutgoingMessage(connection, text)
    data = backend.prepare_message(message)
    assert_equals(data['split'], 3)

