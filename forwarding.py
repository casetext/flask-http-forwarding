import sys
import traceback
import string
import re
import copy
from urllib.parse import urlparse,urlunparse
from threading import Thread
from io import StringIO
import requests
requests.adapters.DEFAULT_RETRIES = 20

from .errors import error

forwarding_timeout = 15
default_headers = {}
required_forwarding_headers = [
    "X-Forward-ID",
    "X-Forward-To",
    "X-Forward-Query-Params",
    "X-Forward-Method",
    "X-Forward-Referer",
    "X-Forward-Errors-To"
]

def headers(header_dict):
    return dict(list(default_headers.items()) + list(header_dict.items()))

class Unforwardable(Exception): pass
class MissingHeaders(Exception): pass
class ResponseError(Exception): pass

def h_list(header):
    """ Convert a comma-separated HTTP header into a Python list. """
    obj = re.split(r",\s*", header)
    new_obj = []
    for item in obj:
        new_obj.append(str(item).replace("%23", ","))
    return new_obj

def list_header(obj):
    """ Convert a Python list into a comma-separated HTTP header. """
    if obj.__class__ not in (list, tuple):
        return str(obj)
    new_obj = []
    for item in obj:
        new_obj.append(str(item).replace(",", "%23"))
    return ", ".join(new_obj)

def encode_headers(out_headers):
    """ Convert a dictionary with Python lists into comma-separated HTTP header values. """
    headers = {}
    for header, value in out_headers.items():
        if value.__class__ in (list, tuple):
            headers[header] = list_header(value)
        else:
            headers[header] = value

        if len(headers[header]) is 0:
            del headers[header]
    return headers

def dispatch_forwarding_request(iri=None, referer="", cookies={}, body="", b_headers={}):
    """ Dispatch a request to the next server in the forwarding list. """
    url = b_headers["X-Forward-To"].pop(0)
    query_params = b_headers["X-Forward-Query-Params"].pop(0)
    method = b_headers["X-Forward-Method"].pop(0).upper()

    scheme, netloc, path, params, old_query, fragment = urlparse(url)
    full_url = urlunparse((
        scheme,
        netloc,
        iri.manifestation_str(),
        params,
        query_params,
        ""
    ))

    b_headers["X-Forward-Referer"] = referer
    b_headers["Content-Type"] = iri.mime_type()
    full_url = full_url.replace("#", "%23")
    
    if body.__class__ == str:
        body = body.encode("utf-8")
    try:
        resp = requests.request(method,
                                full_url,
                                headers=encode_headers(b_headers),
                                cookies=cookies,
                                allow_redirects=True,
                                timeout=forwarding_timeout,
                                data=body)
        if resp.status_code not in (requests.codes.accepted,
                                    requests.codes.created,
                                    requests.codes.ok,
                                    requests.codes.no_content):
            raise ResponseError(resp.status_code, resp.content)
    except ResponseError as e:
        error_url = b_headers.pop("X-Forward-Errors-To")[0]
        b_headers["X-Forward-Error-Condition"] = "External"
        b_headers["X-Forward-Error-Code"] = str(e.args[0])
        b_headers["X-Forward-Error-Message"] = str(e.args[1])
        requests.post(error_url,
                      headers=encode_headers(b_headers),
                      cookies=cookies,
                      allow_redirects=True,
                      timeout=forwarding_timeout,
                      data="")
    except Exception as e:
        # dispatch an error message
        msg = "\n".join(list(str(e)) + traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1],
                sys.exc_info()[2]))
        error_url = b_headers.pop("X-Forward-Errors-To")[0]
        b_headers["X-Forward-Error-Condition"] = "Internal"
        b_headers["X-Forward-Error-Message"] = msg
        requests.post(error_url,
                      headers=encode_headers(b_headers),
                      cookies=cookies,
                      allow_redirects=True,
                      timeout=forwarding_timeout,
                      data="")


def parse_headers(in_headers):
    missing_headers = []
    headers = {}
    for header in required_forwarding_headers:
        if header in in_headers:
            headers[header] = h_list(in_headers[header])
        else:
            missing_headers.append(header)
    # no headers, so we assume it isn't forwardable
    if len(missing_headers) is len(required_forwarding_headers):
        raise Unforwardable()
    elif len(missing_headers) is 0:
        return headers
    else:
        raise MissingHeaders(missing_headers)

def handle_forwarding(response_body, request, new_iri):
    """
    Seamlessly either hand off the response to the next step in the
    forwarding chain, if there is one, or just return it to the client.
    """

    try:
        # DO NOT BLOCK. Dispatch the forwarding request and move on.
        t = Thread(target=dispatch_forwarding_request,
                   kwargs={
                       'referer': request.url,
                       'iri': new_iri,
                       'cookies': request.cookies,
                       'body': response_body,
                       'b_headers': parse_headers(request.headers)
                   })
        t.start()
        resp = ("",
                202,
                headers({
                    "X-Canonical-IRI": new_iri.manifestation_str()
                }))
    except Unforwardable as e:
        resp = (response_body,
                200,
                headers({
                    "X-Canonical-IRI": new_iri.manifestation_str()
                }))
    except MissingHeaders as e:
        missing_headers = e.args[0]
        if len(missing_headers) is 1:
            err_str = "Missing header %s" % missing_headers[0]
        else:
            header_tail_str = "and %s" % missing_headers.pop()
            err_str = "Missing headers %s %s" % (", ".join(missing_headers), header_tail_str)
        resp = error(400, err_str)
    return resp
