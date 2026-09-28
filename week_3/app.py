import json

APP_VERSION = "1.0.0"
MESSAGE = "Hello from week 3 multi stage, build cache"


def app(environ, start_response):
    if environ.get("PATH_INFO", "/") == "/":
        status = "200 OK"
        payload = {
            "application": "course-app",
            "version": APP_VERSION,
            "message": MESSAGE,
        }
    else:
        status = "404 Not Found"
        payload = {"error": "not found"}

    body = (json.dumps(payload) + "\n").encode("utf-8")
    start_response(status, [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(body))),
    ])
    return [body]
