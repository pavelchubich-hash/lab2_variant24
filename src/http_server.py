"""Bottle HTTP API server implementation for Variant 24."""

import os
import subprocess
import sys
import tempfile
from bottle import Bottle, request, response
import data_layer
import xml_utils

HTTP_OK = 200
HTTP_NOT_ACCEPTABLE = 406
HTTP_UNSUPPORTED_MEDIA = 415
EMPTY_LEN = 0
EXIT_SUCCESS = 0
DEFAULT_TIMEOUT_SEC = 10
XML_MIME = "application/xml"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_NONE = "none"


def check_request_headers(method: str, headers: dict) -> tuple:
    """Validate mandatory HTTP request headers per specification."""
    up_method = method.upper()
    c_type = headers.get("Content-Type", "")
    accept_val = headers.get("Accept", "")

    if up_method in ("POST", "PUT", "PATCH"):
        if XML_MIME not in c_type:
            body = xml_utils.serialize_error(
                HTTP_UNSUPPORTED_MEDIA, "Unsupported Media Type"
            )
            return (HTTP_UNSUPPORTED_MEDIA, body)
        if XML_MIME not in accept_val:
            body = xml_utils.serialize_error(
                HTTP_NOT_ACCEPTABLE, "Not Acceptable"
            )
            return (HTTP_NOT_ACCEPTABLE, body)
    else:
        if XML_MIME not in accept_val:
            body = xml_utils.serialize_error(
                HTTP_NOT_ACCEPTABLE, "Not Acceptable"
            )
            return (HTTP_NOT_ACCEPTABLE, body)
    return ()


def enforce_headers(handler_func):
    """Decorator to enforce mandatory HTTP headers on Bottle route."""
    def wrapper(*args, **kwargs):
        err = check_request_headers(request.method, dict(request.headers))
        if len(err) > EMPTY_LEN:
            err_code, err_body = err
            response.status = err_code
            response.content_type = XML_MIME
            return err_body
        response.status = HTTP_OK
        response.content_type = XML_MIME
        return handler_func(*args, **kwargs)
    return wrapper


def execute_computation(data: str, test_mode: bool) -> tuple:
    """Execute CLI minifier via subprocess or return simulated result."""
    if test_mode:
        mock_output = data[:10] if len(data) > 10 else data
        return (mock_output, STATUS_SUCCESS, STATUS_NONE)

    temp_fd, temp_path = tempfile.mkstemp(suffix=".js")
    os.close(temp_fd)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cli_path = os.path.join(script_dir, "minifier.py")

    try:
        proc = subprocess.run(
            [sys.executable, cli_path, "-o", temp_path],
            input=data,
            text=True,
            capture_output=True,
            timeout=DEFAULT_TIMEOUT_SEC,
            check=False,
        )
        if proc.returncode == EXIT_SUCCESS and os.path.exists(temp_path):
            with open(temp_path, "r", encoding="utf-8") as res_f:
                minified_code = res_f.read()
            return (minified_code, STATUS_SUCCESS, STATUS_NONE)
        return ("", STATUS_FAILED, proc.stderr)
    except Exception as exc:
        return ("", STATUS_FAILED, str(exc))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _register_person_routes(app: Bottle, store) -> None:
    """Register person related API routes."""
    @app.route("/public/api/person-make/<identifier>", method="PUT")
    @enforce_headers
    def make_person(identifier: str):
        pid = int(identifier)
        ip = request.query.get("ip", "127.0.0.1")
        platform = request.query.get("platform", "Linux")
        user_agent = request.query.get("user_agent", "Client/1.0")
        store.create_person(pid, ip, platform, user_agent)
        return xml_utils.serialize_id_response(pid)

    @app.route("/public/api/person-remove", method="GET")
    @enforce_headers
    def remove_person():
        pid = int(request.query.get("identifier", "0"))
        ok = store.delete_person(pid)
        return xml_utils.serialize_status_response(ok)

    @app.route("/public/api/person-scan", method="POST")
    @enforce_headers
    def scan_person():
        all_p = store.get_persons()
        ip_filter = request.query.get("ip")
        if ip_filter:
            all_p = [p for p in all_p if p[2] == ip_filter]
        return xml_utils.serialize_persons(all_p)


def _register_command_routes(app: Bottle, store, test_mode: bool) -> None:
    """Register command and result execution API routes."""
    @app.route("/public/api/command-make/<identifier>", method="PUT")
    @enforce_headers
    def make_command(identifier: str):
        cid = int(identifier)
        data = request.query.get("data", "")
        pid = int(request.query.get("person", "0"))
        tags = request.query.get("tags", "")
        status = request.query.get("status", "pending")
        triggered = int(request.query.get("triggered", "0"))
        store.create_command(cid, data, pid, tags, status, triggered)
        res_data, res_status, res_exc = execute_computation(data, test_mode)
        store.create_result(cid, res_data, res_status, res_exc, cid)
        return xml_utils.serialize_id_response(cid)

    @app.route("/public/api/command-remove", method="GET")
    @enforce_headers
    def remove_command():
        cid = int(request.query.get("identifier", "0"))
        ok = store.delete_command(cid)
        return xml_utils.serialize_status_response(ok)

    @app.route("/public/api/command-scan/<person>", method="POST")
    @enforce_headers
    def scan_command(person: str):
        pid = int(person)
        cmds = store.get_commands_by_person(pid)
        return xml_utils.serialize_commands(cmds)


def _register_report_routes(app: Bottle, store) -> None:
    """Register result and report querying API routes."""
    @app.route("/public/api/result-scan/<command>", method="POST")
    @enforce_headers
    def scan_result(command: str):
        cid = int(command)
        res_list = store.get_results_by_command(cid)
        return xml_utils.serialize_results(res_list)

    @app.route("/public/api/report-scan", method="POST")
    @enforce_headers
    def scan_report():
        items = store.select_report_data()
        return xml_utils.serialize_report(items)


def create_app(storage=None, test_mode: bool = False) -> Bottle:
    """Create and configure Bottle application instance."""
    app = Bottle()
    store = storage if storage is not None else data_layer
    _register_person_routes(app, store)
    _register_command_routes(app, store, test_mode)
    _register_report_routes(app, store)
    return app


if __name__ == "__main__":
    app_instance = create_app(test_mode=False)
    app_instance.run(host="127.0.0.1", port=8024, debug=True)
