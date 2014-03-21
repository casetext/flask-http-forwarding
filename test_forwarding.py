import os
import re
import time
import httpretty
import unittest
import socket

from libcasetext.iri import IRI
from app_fixture import app


test_iri = "/us/judgment/us/1986-06-30/05-179/eng@published#test/2014-01-01/main.xml"
test_transform = "mayer-to-akx"
test_xml_file = "./test/data/0b3e349463dcdd20.xml"
test_file = ""
with open(test_xml_file, 'r') as f:
    test_file = f.read()
full_iri = test_iri + "?transform=%s" % test_transform

test_forwarding_headers = {
    "Content-Type": "text/xml",
    "X-Forward-ID": "550e8400-e29b-41d4-a716-446655440000",
    "X-Forward-To": "http://example.com, http://2example.com",
    "X-Forward-Query-Params": "foo=bar&baz=quux, testing=true",
    "X-Forward-Method": "POST, PUT",
    "X-Forward-Errors-To": "http://errors.com",
    "X-Forward-Referer": "ORIGIN"
}

fail_forwarding_headers = {
    "Content-Type": "text/xml",
    "X-Forward-ID": "550e8400-e29b-41d4-a716-446655440000",
    "X-Forward-To": "http://err-gen.com",
    "X-Forward-Query-Params": "foo=bar&baz=quux",
    "X-Forward-Method": "POST",
    "X-Forward-Errors-To": "http://errors.com",
    "X-Forward-Referer": "ORIGIN"
}

timeout_forwarding_headers = {
    "Content-Type": "text/xml",
    "X-Forward-ID": "550e8400-e29b-41d4-a716-446655440000",
    "X-Forward-To": "http://timeout.com",
    "X-Forward-Query-Params": "foo=bar&baz=quux",
    "X-Forward-Method": "POST",
    "X-Forward-Errors-To": "http://errors.com",
    "X-Forward-Referer": "ORIGIN"
}

expected_forwarding_headers = {
    "Content-Type": "text/xml",
    "X-Forward-ID": "550e8400-e29b-41d4-a716-446655440000",
    "X-Forward-To": "http://2example.com",
    "X-Forward-Query-Params": "testing=true",
    "X-Forward-Method": "PUT",
    "X-Forward-Errors-To": "http://errors.com",
    "X-Forward-Referer": "http://localhost" + full_iri
}

class TestForwarding(unittest.TestCase):
    def setUp(self):
        self.flask_app_obj = app
        self.app = self.flask_app_obj.test_client()
        httpretty.enable()
        self.response_count = 0
        self.error_count = 0
        def callback(request, uri, headers):
            self.assertEqual(request.body.decode('utf8'), test_file)
            for expected_header, value in expected_forwarding_headers.items():
                self.assertIn(expected_header, request.headers)
                self.assertEqual(request.headers[expected_header], value)

            self.response_count += 1
            return (202, headers, "")
        def err_callback(request, uri, headers):
            self.error_count += 1
            return (200, headers, "")

        httpretty.register_uri(httpretty.POST,
                               re.compile("example.com/(.*)$"),
                               body=callback)
        httpretty.register_uri(httpretty.POST,
                               re.compile("errors.com/(.*)$"),
                               body=callback)

    def test_without_forwarding(self):
        """ Not setting forwarding headers should trigger a 200. """
        full_iri = test_iri + "?transform=%s" % test_transform
        with open(test_xml_file, 'r') as f:
            r = self.app.post(full_iri, data=f.read(), headers={
                "Content-Type": "application/xml"
            })
            self.assertEqual(r.status_code, 200)

    def test_with_bad_headers(self):
        """ Failing to set any one of the forwarding headers should trigger a 400. """
        for i in range(0, len(test_forwarding_headers)):
            items = list(test_forwarding_headers.items())
            missing_header = items.pop(i)

            # we can't not set the Content-Type, so skip that one
            if missing_header[0] == "Content-Type":
                continue

            shortened_headers = dict(items)
            for header, value in shortened_headers.items():
                with open(test_xml_file, 'r') as f:
                    r = self.app.post(full_iri, data=f.read(), headers=shortened_headers)
                    self.assertEqual(r.status, "400 Missing header %s" % missing_header[0])

    def test_with_valid_forwarding_scheme(self):
        """ With a valid forwarding scheme in place, we should get a 202.
            We should also expect the dummy HTTP server to get hit correctly. """
        with open(test_xml_file, 'r') as f:
            r = self.app.post(full_iri, data=f.read(), headers=test_forwarding_headers)
            self.assertEqual(r.status_code, 202, r.status)
            time.sleep(0.5)
            self.assertEqual(self.error_count, 0)
            self.assertEqual(self.response_count, 1)

class TestForwardingErrors(unittest.TestCase):
    def setUp(self):
        self.flask_app_obj = app
        self.app = self.flask_app_obj.test_client()
        httpretty.enable()
        self.error_provocation_count = 0
        self.error_response_count = 0

        def provoke_timeout_error(request, uri, headers):
            raise socket.timeout('timeout')
            return (200, headers, "OK")

        def provoke_error_callback(request, uri, headers):
            self.error_provocation_count += 1
            return (500, headers, "ERROR!")

        def handle_error_callback(request, uri, headers):
            self.error_response_count += 1
            return (200, headers, "OK")

        httpretty.register_uri(httpretty.POST,
                               re.compile("err-gen.com/(.*)$"),
                               body=provoke_error_callback)
        httpretty.register_uri(httpretty.POST,
                               re.compile("errors.com/(.*)$"),
                               body=handle_error_callback)
        httpretty.register_uri(httpretty.POST,
                               re.compile("timeout.com/(.*)$"),
                               body=provoke_timeout_error)

    def test_error_handling(self):
        """ If a forward fails, we should see a message to the error-handling server. """
        with open(test_xml_file, 'r') as f:
            r = self.app.post(full_iri, data=f.read(), headers=fail_forwarding_headers)
            self.assertEqual(r.status_code, 202, r.status)
            time.sleep(0.5)
            self.assertEqual(self.error_provocation_count, 1)
            self.assertEqual(self.error_response_count, 1)
    def test_timeout_handling(self):
        """ If a forwarding times out, we should see a message to the error-handling server. """
        with open(test_xml_file, 'r') as f:
            r = self.app.post(full_iri, data=f.read(), headers=timeout_forwarding_headers)
            self.assertEqual(r.status_code, 202, r.status)
            time.sleep(0.5)
            self.assertEqual(self.error_response_count, 1)
