rmach
==============

Basic `Mach <http:/http://www.mach.com/>`_ backend for the `RapidSMS <http://www.rapidsms.org/>`_ project.

Usage
----------

Add rmach to your Python path and setup the backend in your Django settings file. For example::

    INSTALLED_BACKENDS = {
        "mach": {
            "ENGINE": "rmach.backend",
            'host': 'localhost', 'port': '8888', # used for spawned backend WSGI server
            'config': {
                'id': 'XXXX',
                'password': 'YYYYYYYY',
                'number': '(###) ###-####',
                'encoding': 'UTF-8', # optional message encoding
                'encoding_errors': 'ignore', # optional encoding handling 
            }
        },
    }
