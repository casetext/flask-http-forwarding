import logging
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
