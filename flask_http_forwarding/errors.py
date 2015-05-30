import logging, socket, json
from flask import Response

error_logger = logging.getLogger('Flask-HTTP-Forwarding.errors')

def error(code, message, body=None):
    errmsg = "%d %s: %s" % (code, message, body) if body else "%d %s" % (code, message)
    error_logger.error(errmsg)

    if body is None:
        body = "%s\n" % message
    return Response(
        status="%d %s" % (code, message),
        response=body,
        mimetype="text/plain",
        headers={}
    )

def log_errors_without_request_context(headers, iri, message_payload):
    fixed_payload = {
        'id': headers.pop('X-Forward-Id')[0],
        'iri': iri.manifestation_str(),
        'levelname': 'ERROR',
        'filename': __file__,
        'host': socket.gethostbyname( socket.gethostname() )
    }

    payload = dict(list(fixed_payload.items()) + list(message_payload.items()))

    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # temporarily, because of stupid flesichwolf, we have to strip the http off the front of the url.
    schema, remainder = headers.pop('X-Forward-Errors-To')[0].split('://')
    address,port = remainder.split(':')
    conn.sendto( json.dumps( payload ).encode('utf-8'), (address,int(port),) )
