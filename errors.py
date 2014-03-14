from flask import Response

def error(code, message, body=None):
    if body is None:
        body = "%s\n" % message
    return Response(
        status="%d %s" % (code, message),
        response=body,
        mimetype="text/plain",
        headers={}
    )
