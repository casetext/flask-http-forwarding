from flask import Flask, request

from libcasetext.iri import IRI
from libcasetext.flask_utils import handle_forwarding

app = Flask(__name__)
@app.route("/<path:p>", methods=["POST"])
def test_handler(p):
    return handle_forwarding(request.data.decode("utf-8"), request, IRI(request.path))

if __name__ == "__main__":
    app.run(debug=True)
