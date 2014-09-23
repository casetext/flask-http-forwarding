flask-http-forwarding
=====================

[![Build Status](https://travis-ci.org/casetext/flask-http-forwarding.svg?branch=master)](https://travis-ci.org/casetext/flask-http-forwarding)

Flask extension implementing HTTP forwarding

This flask makes it possible to implement an HTTP forwarding system using Flask.

### FORWARDING

HTTP forwarding is how Fleischwolf handles mass queries of documents.

To use it, you'll need to start by setting forwarding headers in the following format:
```
X-Forward-Id: 12345678-1234-1234-1234-1234567890AB
X-Forward-Errors-To: http://errors.com
X-Forward-Referer: http://previous-server.com
X-Forward-To: http://nextserver.com
X-Forward-Query-Params: foo=bar
X-Forward-Method: POST
```

The first 3 headers are mandatory for all connections:
 - ```X-Forward-Id``` is a conventional 128-bit UUID. It uniquely identifies the forwarding request.
 - ```X-Forward-Errors-To``` is the server that error messages should be dispatched to.
 - ```X-Forward-Referer``` is the name of the preceding server.  
If you're dispatching the reuqest manually, you can set the last of these to ORIGIN.

The remaining 3 are required to initiate forwarding:
 - ```X-Forward-To``` is the HTTP hostname of the next server in the forwarding chain.
 - ```X-Forward-Query-Params``` should hold any query params you want to be set on the URL pulled by X-Forward-To.
 - ```X-Forward-Method``` is the HTTP verb used in the forwarded request. Only PUT and POST are supported.

You can set as many different forwarding destinations as you like in X-Forward-To. So for instance, if you were to send the following headers:
```
...
X-Forward-To: http://one.com, http://two.com, http://three.com
X-Forward-Query-Params: foo=bar, flavor=lemon&color=yellow, loneliest_number=1
X-Forward-Method: POST, POST, PUT
...
```

The request will be forwarded as a POST to one.com, then as a PUT from one.com to two.com, then as a POST from two.com to three.com. The IRI will have the query parameters appended, so if you were monitoring the server logs for all three hosts, you'd see something like this:
- POST http://one.com/us/judgment/us/1986-06-30/05-274/eng@published#test/2014-01-01/main.xml?foo=bar
- POST http://three.com/us/judgment/us/1986-06-30/05-274/eng@published#test/2014-01-01/main.xml?loneliest_number=1
- PUT http://two.com/us/judgment/us/1986-06-30/05-274/eng@published#test/2014-01-01/main.xml?flavor=lemon&color=yellow

In keeping with HTTP semantic convention, a PUT is a store, and a POST is an action.  Therefore, a PUT should generally be a terminal action, specifying that the output should be stored as the final step in the chain.
