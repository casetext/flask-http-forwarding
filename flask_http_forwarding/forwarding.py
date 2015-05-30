import sys
import traceback
import string
import re
import copy

from flask import current_app

# We don't support python 2, but attempt to make it work.
if sys.version_info[0] < 3:
    from urlparse import urlparse,urlunparse
    print( "DANGER WILL ROBINSON: You are running python 2, which is unsupported. YMMV." )
else:
    from urllib.parse import urlparse,urlunparse
    from functools import reduce

#from threading import Thread
import threading
from io import StringIO
import logging
import requests
requests.adapters.DEFAULT_RETRIES = 20

from .errors import error, log_errors_without_request_context

fwding_log = logging.getLogger('Flask-HTTP-Forwarding.forwarding')

forwarding_timeout = 120
required_forwarding_headers = {
    'fixed': [
        "X-Forward-Id",
        "X-Forward-Referer",
        "X-Forward-Errors-To"
        ],
    'to-forward': [
        "X-Forward-To",
        "X-Forward-Query-Params",
        "X-Forward-Method"
        ]
    }

def headers(header_dict):
    default_headers = current_app.config.get('DEFAULT_HEADERS') or {}
    return dict(list(default_headers.items()) + list(header_dict.items()))

class Unforwardable(Exception): pass
class MissingHeaders(Exception): pass
class ResponseError(Exception): pass

def h_list(header):
    """ Convert a comma-separated HTTP header into a Python list. """
    if header.__class__ in (list, tuple):
        return list(header)

    obj = re.split(r",\s*", header)
    new_obj = []
    for item in obj:
        new_obj.append(str(item))
    return new_obj

def list_header(obj):
    """ Convert a Python list into a comma-separated HTTP header. """
    if obj.__class__ not in (list, tuple):
        return str(obj)

    new_obj = []
    for item in obj:
        new_obj.append(str(item))
    return ",".join(new_obj)

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

def parse_headers(in_headers):
    missing_headers = []
    headers = {}
    for header in reduce( lambda a,b: a+b, required_forwarding_headers.values() ):
        if header in in_headers:
            headers[header] = h_list(in_headers[header])
        else:
            missing_headers.append(header)
    # no headers, so we assume it isn't forwardable
    if set(missing_headers)==set(required_forwarding_headers['to-forward']):
        raise Unforwardable()
    elif len(missing_headers) is 0:
        return headers
    else:
        raise MissingHeaders(missing_headers)

def concat_headers(old, new):
    retval = dict(old.items())
    for k in new.keys():
        if old.get(k):
            steps = [ s for s in old[k].split(',') if s ]
            if old[k][-1]==',':
                steps.append( new[k] )
            else:
                steps[-1] += '&%s' % new[k]
            retval[k] = ','.join(steps)
        else:
            retval[k] = new[k]

    return retval


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
    
    if body.__class__ == str and sys.version_info[0]==3:
        body = body.encode("utf-8")
    elif sys.version_info[0]==2 and body.__class__ == unicode:
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
        message_payload = {
            "errorType": "External",
            "errorCode": str(e.args[0]),
            "errorMessage": str(e.args[1]),
            "responseText": resp.text
        }
        log_errors_without_request_context(b_headers,
                                           iri,
                                           message_payload)
    except Exception as e:
        trace = "\n".join(list(str(e)) + traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1],
                                                                    sys.exc_info()[2]))
        message_payload = {
            "errorType": "Internal",
            "errorMessage": trace
        }
        log_errors_without_request_context(b_headers,
                                           iri,
                                           message_payload)


def handle_forwarding(response_body, request, new_iri, user_headers={}):
    """
    Seamlessly either hand off the response to the next step in the
    forwarding chain, if there is one, or just return it to the client.
    """

    try:
        user_headers = concat_headers(request.headers, user_headers)
        # DO NOT BLOCK. Dispatch the forwarding request and move on.
        t = threading.Thread(target=dispatch_forwarding_request,
                   kwargs={
                       'referer': request.url,
                       'iri': new_iri,
                       'cookies': request.cookies,
                       'body': response_body,
                       'b_headers': parse_headers(user_headers)
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
