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
                'timeout': 8, # optional gateway timeout in seconds
            }
        },
    }


Running Tests
----------------

To run the test suite you need to install django, rapidsms and django_nose. You can then
run the test suite using `django-admin.py`:

    django-admin.py test rmach --settings=test_settings

