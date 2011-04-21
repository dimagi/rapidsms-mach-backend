DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "test.db",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
    }
}

INSTALLED_APPS = [
    "django_nose",
    "rapidsms",
    "rmach",
]

TEST_RUNNER = "django_nose.NoseTestSuiteRunner"
