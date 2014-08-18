# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

EXCLUDE_FROM_PACKAGES = ['test_*',]
MAJOR_VERSION = "1.0"
VERSION = MAJOR_VERSION + '-' + os.popen('git log --oneline | wc -l').read().strip()

INSTALL_REQUIRES = [
    'requests',
    'httpretty',
    'Flask'
]

TESTS_REQUIRE = [
    'nose',
]

setup(
    name='Flask-HTTP-Forwarding',
    version=VERSION,
    url='http://www.github.com/casetext/flask-http-forwarding',
    author='J2H2, Inc.',
    author_email='casetext@casetext.com',
    description='Flask extension implementing HTTP forwarding',
    license='MIT',
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    test_suite="nose.collector",
    platforms='any',
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)