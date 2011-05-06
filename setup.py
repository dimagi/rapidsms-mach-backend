from setuptools import setup, find_packages

setup(
    name='rmach',
    version='0.2.2',
    author='Dimagi',
    packages=find_packages(),
    include_package_data=True,
    exclude_package_data={
        '': ['*.sql', '*.pyc'],
    },
    url='https://github.com/dimagi/rapidsms-mach-backend',
    description='RapidSMS Mach Backend',
    long_description=open('README.rst').read(),
)
