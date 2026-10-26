"""HTTP API Client implementation matching Table 24 routes."""

import io
import urllib.parse
import urllib.request
import xml_utils

XML_MIME = "application/xml"
STATUS_OK = 200
DEFAULT_PORT = 8024
DEFAULT_HOST = "127.0.0.1"
EMPTY_BYTES_LEN = 0
INDEX_BODY = 2


def execute_wsgi_call(app, method: str, path: str, query: str, headers: dict):
    """Execute in-process WSGI call against Bottle application."""
    captured = {}

    def start_response(status, response_headers, exc_info=None):
        captured["status"] = int(status.split()[0])
        captured["headers"] = dict(response_headers)

    env = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.StringIO(),
        "SERVER_NAME": DEFAULT_HOST,
        "SERVER_PORT": str(DEFAULT_PORT),
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "CONTENT_LENGTH": str(EMPTY_BYTES_LEN),
    }
    for key, val in headers.items():
        k_upper = key.upper().replace("-", "_")
        env_key = (
            "CONTENT_TYPE" if k_upper == "CONTENT_TYPE" else f"HTTP_{k_upper}"
        )
        env[env_key] = val

    body_chunks = app(env, start_response)
    body_text = b"".join(body_chunks).decode("utf-8")
    status_code = captured.get("status", STATUS_OK)
    res_headers = captured.get("headers", {})
    return status_code, res_headers, body_text


def execute_network_call(
    base_url: str, method: str, path: str, query: str, headers: dict
):
    """Execute real HTTP network call via urllib."""
    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{query}"
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            resp_headers = dict(resp.getheaders())
            body_text = resp.read().decode("utf-8")
            return status, resp_headers, body_text
    except urllib.error.HTTPError as err:
        return err.code, dict(err.headers), err.read().decode("utf-8")


class HTTPClient:
    """Client for interacting with Table 24 HTTP API endpoints."""

    def __init__(self, base_url: str = None, app=None):
        """Initialize client with either base URL or Bottle app."""
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            self.base_url = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"
        self.app = app
        self.headers = {"Content-Type": XML_MIME, "Accept": XML_MIME}

    def request(
        self,
        method: str,
        path: str,
        params: dict = None,
        override_headers: dict = None,
    ) -> tuple:
        """Perform request and return status, headers, and body."""
        headers = dict(self.headers)
        if override_headers is not None:
            headers = override_headers
        q_str = urllib.parse.urlencode(params) if params else ""
        if self.app is not None:
            return execute_wsgi_call(self.app, method, path, q_str, headers)
        return execute_network_call(
            self.base_url, method, path, q_str, headers
        )

    def public_api_person_make(
        self,
        identifier: int,
        ip: str,
        platform: str,
        user_agent: str,
        headers: dict = None,
    ) -> dict:
        """Call PUT /public/api/person-make/:identifier."""
        path = f"/public/api/person-make/{identifier}"
        params = {"ip": ip, "platform": platform, "user_agent": user_agent}
        res = self.request(
            "PUT", path, params=params, override_headers=headers
        )
        return xml_utils.parse_xml_to_dict(res[INDEX_BODY])

    def public_api_person_remove(
        self, identifier: int, headers: dict = None
    ) -> dict:
        """Call GET /public/api/person-remove."""
        path = "/public/api/person-remove"
        params = {"identifier": identifier}
        res = self.request(
            "GET", path, params=params, override_headers=headers
        )
        return xml_utils.parse_xml_to_dict(res[INDEX_BODY])

    def public_api_person_scan(
        self, filters: dict = None, headers: dict = None
    ) -> list:
        """Call POST /public/api/person-scan."""
        path = "/public/api/person-scan"
        res = self.request(
            "POST", path, params=filters, override_headers=headers
        )
        return xml_utils.parse_xml_items(res[INDEX_BODY], "person")

    def public_api_command_make(
        self,
        identifier: int,
        data: str,
        person: int,
        tags: str,
        status: str,
        triggered: int,
        **kwargs,
    ) -> dict:
        """Call PUT /public/api/command-make/:identifier."""
        headers = kwargs.get("headers")
        path = f"/public/api/command-make/{identifier}"
        params = {
            "data": data,
            "person": person,
            "tags": tags,
            "status": status,
            "triggered": triggered,
        }
        res = self.request(
            "PUT", path, params=params, override_headers=headers
        )
        return xml_utils.parse_xml_to_dict(res[INDEX_BODY])

    def public_api_command_remove(
        self, identifier: int, headers: dict = None
    ) -> dict:
        """Call GET /public/api/command-remove."""
        path = "/public/api/command-remove"
        params = {"identifier": identifier}
        res = self.request(
            "GET", path, params=params, override_headers=headers
        )
        return xml_utils.parse_xml_to_dict(res[INDEX_BODY])

    def public_api_command_scan(
        self, person: int, filters: dict = None, headers: dict = None
    ) -> list:
        """Call POST /public/api/command-scan/:person."""
        path = f"/public/api/command-scan/{person}"
        res = self.request(
            "POST", path, params=filters, override_headers=headers
        )
        return xml_utils.parse_xml_items(res[INDEX_BODY], "command")

    def public_api_result_scan(
        self, command: int, filters: dict = None, headers: dict = None
    ) -> list:
        """Call POST /public/api/result-scan/:command."""
        path = f"/public/api/result-scan/{command}"
        res = self.request(
            "POST", path, params=filters, override_headers=headers
        )
        return xml_utils.parse_xml_items(res[INDEX_BODY], "result")

    def public_api_report_scan(self, headers: dict = None) -> list:
        """Call POST /public/api/report-scan."""
        path = "/public/api/report-scan"
        res = self.request("POST", path, override_headers=headers)
        return xml_utils.parse_xml_items(res[INDEX_BODY], "item")

    public_api_person_make_identifier = public_api_person_make
    _public_api_person_make_identifier = public_api_person_make
    _public_api_person_remove = public_api_person_remove
    _public_api_person_scan = public_api_person_scan
    public_api_command_make_identifier = public_api_command_make
    _public_api_command_make_identifier = public_api_command_make
    _public_api_command_remove = public_api_command_remove
    public_api_command_scan_person = public_api_command_scan
    _public_api_command_scan_person = public_api_command_scan
    public_api_result_scan_command = public_api_result_scan
    _public_api_result_scan_command = public_api_result_scan
    _public_api_report_scan = public_api_report_scan
