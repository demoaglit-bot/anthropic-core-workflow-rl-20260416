from environment import handle_request


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("PATH_INFO", "/")
    length = int(environ.get("CONTENT_LENGTH") or 0)
    raw = environ["wsgi.input"].read(length) if length else b""
    payload = None
    if raw:
        payload = __import__("json").loads(raw.decode("utf-8"))

    status, headers, body = handle_request(method, path, payload)
    status_line = f"{int(status)} {status.phrase}"
    start_response(status_line, list(headers.items()))
    return [body]
