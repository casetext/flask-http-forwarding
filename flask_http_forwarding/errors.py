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

def log_errors_without_request_context(headers, iri, message):
    payload = {
        'id': headers['X-Forward-Id'],
        'iri': iri.manifestation_str(),
        'message': message,
        'levelname': 'ERROR',
        'filename': __file__,
        'host': socket.gethostbyname( socket.gethostname() )
    }

    conn = socket.connect( headers['X-Forward-Errors-To'] )
    socket.sendall( json.dumps( payload ) )
