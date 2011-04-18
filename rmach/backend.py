import datetime
import urllib
import urllib2


from django import http
from django.core.exceptions import ImproperlyConfigured

from rapidsms.backends.http import RapidHttpBackend


class MachImproperlyConfigured(ImproperlyConfigured):
    pass


class MachBackend(RapidHttpBackend):

    def configure(self, host="localhost", port=8080, config=None, **kwargs):
        if "params_incoming" not in kwargs:
            kwargs["params_incoming"] = "snr=%(phone_number)s&msg=%(message)s"
        if "params_outgoing" not in kwargs:
            kwargs["params_outgoing"] = "dnr=%(phone_number)s&msg=%(message)s"
        if "gateway_url" not in kwargs:
            kwargs["gateway_url"] = "http://gw1.promessaging.com/sms.php"
        super(MachBackend, self).configure(host, port, **kwargs)
        self.config = config
        if 'id' not in self.config:
            raise MachImproperlyConfigured(u"Mach backend missing account id")
        if 'password' not in self.config:
            raise MachImproperlyConfigured(u"Mach backend missing account password")
        if 'number' not in self.config:
            raise MachImproperlyConfigured(u"Mach backend missing account number")

    def handle_request(self, request):
        if request.method != 'POST':
            self.info(u"Received request but wasn't POST. Doing nothing: %s" % request.GET)
            return http.HttpResponseNotAllowed(['POST'])
        self.info(u"Received request: %s" % request.POST)
        msg = self.message(request.POST)
        if msg:
            self.route(msg)
            return http.HttpResponse("OK")
        else:
            return http.HttpResponseBadRequest("")

    def message(self, data):
        encoding = self.config.get('encoding', 'ascii')
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
        encoding = self.config.get('encoding', 'ascii')
        encoding_errors = self.config.get('encoding_errors', 'ignore')
        data = {
            "snr": self.config['number'],
            "id": self.config['id'],
            "pw": self.config['password'],
            "dnr": message.connection.identity,
            "msg": message.text.encode(encoding, encoding_errors),
        }
        return data

    def send(self, message):
        self.info(u"Sending message: %s" % message)
        data = self.prepare_message(message)
        self.debug(u"Sending data: %s" % data)
        try:
            response = urllib2.urlopen(self.gateway_url, urllib.urlencode(data))
            for line in response:
                if "-ERR" in line:
                    # fail
                    self.error(u"Error from gateway: %s" % line)
                    self.debug(response)
                    return False
        except Exception, e:
            self.exception(e)
            return False
        self.info('SENT')
        self.debug(response)
        return True
