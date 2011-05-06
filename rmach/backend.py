import datetime
import hashlib
import math
import socket
import urllib
import urllib2

from django import http
from django.core.exceptions import ImproperlyConfigured

from rapidsms.backends.http import RapidHttpBackend


class MachImproperlyConfigured(ImproperlyConfigured):
    pass


class MachBackend(RapidHttpBackend):
    max_ascii_length = 160
    max_unicode_length = 70
    default_timeout = 8
    gateway_url = "http://gw1.promessaging.com/sms.php"
    backup_url = "http://gw2.promessaging.com/sms.php"

    def configure(self, host="localhost", port=8080, config=None, **kwargs):
        if "params_incoming" not in kwargs:
            kwargs["params_incoming"] = "snr=%(phone_number)s&msg=%(message)s"
        if "params_outgoing" not in kwargs:
            kwargs["params_outgoing"] = "dnr=%(phone_number)s&msg=%(message)s"
        if "gateway_url" not in kwargs:
            kwargs["gateway_url"] = self.gateway_url
        super(MachBackend, self).configure(host, port, **kwargs)
        self.config = config
        if 'id' not in self.config:
            raise MachImproperlyConfigured(u"Mach backend missing account id")
        if 'password' not in self.config:
            raise MachImproperlyConfigured(u"Mach backend missing account password")
        if 'number' not in self.config:
            raise MachImproperlyConfigured(u"Mach backend missing account number")

    def handle_request(self, request):
        if request.method != 'GET':
            self.info(u"Received request but wasn't GET. Doing nothing: %s" % request.POST)
            return http.HttpResponseNotAllowed(['GET'])
        self.info(u"Received request: %s" % request.GET)
        msg = self.message(request.GET)
        if msg:
            self.route(msg)
            return http.HttpResponse("OK")
        else:
            return http.HttpResponseBadRequest("")

    def message(self, data):
        encoding = self.config.get('encoding', 'UTF-8')
        encoding_errors = self.config.get('encoding_errors', 'ignore')
        sms = data.get(self.incoming_message_param, '')
        sms = sms.decode(encoding, encoding_errors)
        sender = data.get(self.incoming_phone_number_param, '')
        if not sms or not sender:
            error_msg = u"ERROR: Missing %(msg)s or %(phone_number)s. parameters received are: %(params)s" % {
                "msg" : self.incoming_message_param, 
                "phone_number": self.incoming_phone_number_param,
                "params": unicode(data)
            }
            self.error(error_msg)
            return None
        now = datetime.datetime.utcnow()
        try:
            msg = super(MachBackend, self).message(sender, sms, now)
        except Exception, e:
            self.exception(e)
            raise
        return msg

    def prepare_message(self, message):
        sender = self.config['number']
        destination = message.connection.identity
        msg = message.text
        is_ascii = self._is_ascii(msg)
        length = len(msg)
        if not is_ascii:
            msg = msg.encode('UTF-16', 'ignore')
        if not destination.startswith("+"):
            destination = u"+%s" % destination
        password = self.config['password']
        data = {
            "snr": sender,
            "id": self.config['id'],
            "pw": password,
            "dnr": destination,
            "msg": msg,
            "test": self.config.get('test', 0)
        }
        if not is_ascii:
            data['encoding'] = 'ucs'
            if length > self.max_unicode_length:
                data["split"] = math.ceil(length / float(self.max_unicode_length))
        elif length > self.max_ascii_length:
            data["split"] = math.ceil(length / float(self.max_ascii_length))
        return data

    def _is_ascii(self, msg):
        try:
            test = msg.encode('ascii', 'strict')
            return True
        except UnicodeEncodeError:
            return False

    def send(self, message):
        self.info(u"Sending message: %s" % message)
        data = self.prepare_message(message)
        self.debug(u"Sending data: %s" % data)
        timeout = self.config.get('timeout', self.default_timeout)
        encoded_data = urllib.urlencode(data)
        for url in [self.gateway_url, self.backup_url]:
            try:
                response = urllib2.urlopen(url, encoded_data, timeout)
                for line in response:
                    if "-ERR" in line:
                        # fail
                        self.error(u"Error from gateway: %s" % line)
                        return False
            except urllib2.URLError, e:
                if isinstance(e.reason, socket.timeout):
                    self.error(u"Gateway timeout: %s" % url)
                    # Try the next gateway url
                    continue
                else:
                    self.exception(e)
                    return False
            except Exception, e:
                self.exception(e)
                return False
            self.info('SENT')
            return True
        return False
