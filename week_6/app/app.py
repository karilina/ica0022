import json
import os
import sys

import psycopg

APP_VERSION = "1.2.0"
MESSAGE = "Hello from week 6"


def connect():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=3,
    )


def record_visit():
    with connect() as connection:
        row = connection.execute(
            "UPDATE counter SET visits = visits + 1 "
            "WHERE id = 1 RETURNING visits"
        ).fetchone()
        if row is None:
            raise psycopg.DatabaseError("Counter row is missing")
        return row[0]


def check_database():
    with connect() as connection:
        connection.execute("SELECT 1").fetchone()


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET")
    headers = [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Cache-Control", "no-store"),
    ]

    if path == "/healthz":
        # Liveness: the process is running. Never touches the database.
        status = "200 OK"
        payload = {"status": "alive", "version": APP_VERSION}
    elif path == "/readyz":
        # Readiness: can this Pod do its job right now?
        try:
            check_database()
            status = "200 OK"
            payload = {"status": "ready"}
        except psycopg.Error as error:
            print(f"Readiness check failed: {error}", file=sys.stderr, flush=True)
            status = "503 Service Unavailable"
            payload = {"status": "not ready", "reason": "database unavailable"}
    elif path != "/":
        status = "404 Not Found"
        payload = {"error": "not found"}
    elif method != "GET":
        status = "405 Method Not Allowed"
        payload = {"error": "use GET for this demonstration"}
        headers.append(("Allow", "GET"))
    else:
        try:
            visits = record_visit()
            status = "200 OK"
            payload = {
                "application": "ica0022-app",
                "version": APP_VERSION,
                "message": MESSAGE,
                "visits": visits,
            }
        except psycopg.Error as error:
            print(f"Database error: {error}", file=sys.stderr, flush=True)
            status = "503 Service Unavailable"
            payload = {"error": "database unavailable; inspect the app logs"}

    body = (json.dumps(payload) + "\n").encode("utf-8")
    headers.append(("Content-Length", str(len(body))))
    start_response(status, headers)
    return [body]
