from flask import Flask, request
from flask_http_forwarding.forwarding import handle_forwarding

class IRI(object):
    def __init__(self, iri):
        self.iri_str = iri

    def manifestation_str(self):
        return self.iri_str

    def mime_type(self):
        return "text/xml"

app = Flask(__name__)
@app.route("/<path:p>", methods=["POST"])
def test_handler(p):
    return handle_forwarding(request.data.decode("utf-8"), request, IRI(request.path))

if __name__ == "__main__":
    app.run(debug=True)
