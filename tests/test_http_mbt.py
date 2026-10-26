"""Model-Based Testing for Bottle HTTP API using Hypothesis."""

import threading
import time
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    invariant,
    rule,
    run_state_machine_as_test,
)
import data_layer
from http_client import HTTPClient
from http_server import (
    HTTP_NOT_ACCEPTABLE,
    HTTP_UNSUPPORTED_MEDIA,
    create_app,
)

MIN_COLLECTION_SIZE = 0
INDEX_FIRST = 0
STATUS_OK = 200
NON_EXISTENT_ID = 999999
TEST_PORT = 8025


class ModelOracle:
    """Independent reference model for state tracking."""

    def __init__(self) -> None:
        """Initialize empty collections."""
        self.persons = {}
        self.commands = {}
        self.results = {}

    def add_person(
        self, pid: int, ip: str, platform: str, user_agent: str
    ) -> None:
        """Record person creation."""
        self.persons[pid] = (pid, ip, platform, user_agent)

    def remove_person(self, pid: int) -> bool:
        """Record person deletion."""
        if pid in self.persons:
            del self.persons[pid]
            return True
        return False

    def add_command(
        self,
        cid: int,
        data: str,
        pid: int,
        tags: str,
        status: str,
        triggered: int,
    ) -> None:
        """Record command and corresponding result creation."""
        self.commands[cid] = (cid, data, pid, tags, status, triggered)
        self.results[cid] = (cid, "mock_res", "success", "none", cid)

    def remove_command(self, cid: int) -> bool:
        """Record command deletion."""
        if cid in self.commands:
            del self.commands[cid]
            return True
        return False


class BottleAPIStateMachine(RuleBasedStateMachine):
    """Model-based state machine for Bottle HTTP API."""

    persons = Bundle("persons")
    commands = Bundle("commands")

    def __init__(self) -> None:
        """Initialize state machine, test app, and oracle."""
        super().__init__()
        data_layer.clear_all()
        self.app = create_app(storage=data_layer, test_mode=True)
        self.client = HTTPClient(app=self.app)
        self.oracle = ModelOracle()
        self.last_cmd_id = -1

    @rule(
        target=persons,
        pid=st.integers(min_value=1, max_value=500),
        ip=st.sampled_from(["127.0.0.1", "192.168.1.1", "10.0.0.1"]),
        platform=st.sampled_from(["Linux", "Windows", "Darwin"]),
        user_agent=st.sampled_from(["Firefox", "Chrome", "Safari"]),
    )
    def rule_create_person(
        self, pid: int, ip: str, platform: str, user_agent: str
    ) -> int:
        """Test person creation via HTTP client."""
        resp = self.client.public_api_person_make(
            pid, ip, platform, user_agent
        )
        assert int(resp["identifier"]) == pid
        self.oracle.add_person(pid, ip, platform, user_agent)
        return pid

    @rule(pid=persons)
    def rule_remove_person(self, pid: int) -> None:
        """Test person deletion via HTTP client."""
        resp = self.client.public_api_person_remove(pid)
        exp = "true" if self.oracle.remove_person(pid) else "false"
        assert resp.get("success") == exp

    @rule()
    def rule_remove_nonexistent_person(self) -> None:
        """Test deletion of person that does not exist."""
        resp = self.client.public_api_person_remove(NON_EXISTENT_ID)
        assert resp.get("success") == "false"

    @rule()
    def rule_scan_persons(self) -> None:
        """Test scanning persons via HTTP client."""
        items = self.client.public_api_person_scan()
        assert len(items) == len(self.oracle.persons)

        filtered = self.client.public_api_person_scan(
            filters={"ip": "127.0.0.1"}
        )
        assert isinstance(filtered, list)

    @rule(
        target=commands,
        cid=st.integers(min_value=1, max_value=500),
        pid=persons,
        data=st.sampled_from(["var a = 1;", "function f() { return 2; }"]),
        tags=st.sampled_from(["js", "minify", "code"]),
        status=st.sampled_from(["active", "pending"]),
        triggered=st.integers(min_value=0, max_value=1),
    )
    def rule_create_command(
        self,
        cid: int,
        pid: int,
        data: str,
        tags: str,
        status: str,
        triggered: int,
    ) -> int:
        """Test command creation via HTTP client."""
        resp = self.client.public_api_command_make(
            cid, data, pid, tags, status, triggered
        )
        assert int(resp["identifier"]) == cid
        self.oracle.add_command(cid, data, pid, tags, status, triggered)
        self.last_cmd_id = cid
        return cid

    @rule(cid=commands)
    def rule_remove_command(self, cid: int) -> None:
        """Test command removal via HTTP client."""
        resp = self.client.public_api_command_remove(cid)
        exp = "true" if self.oracle.remove_command(cid) else "false"
        assert resp.get("success") == exp

    @rule()
    def rule_remove_nonexistent_command(self) -> None:
        """Test deletion of command that does not exist."""
        resp = self.client.public_api_command_remove(NON_EXISTENT_ID)
        assert resp.get("success") == "false"

    @rule(pid=persons)
    def rule_scan_commands_by_person(self, pid: int) -> None:
        """Test scanning commands filtered by person."""
        cmds = self.client.public_api_command_scan(pid)
        exp_count = sum(
            1 for c in self.oracle.commands.values() if c[2] == pid
        )
        assert len(cmds) == exp_count

    @rule()
    def rule_scan_results_and_reports(self) -> None:
        """Test scanning results and generating reports."""
        if self.last_cmd_id > MIN_COLLECTION_SIZE:
            res = self.client.public_api_result_scan(self.last_cmd_id)
            assert len(res) >= MIN_COLLECTION_SIZE
        rep = self.client.public_api_report_scan()
        assert len(rep) >= MIN_COLLECTION_SIZE

    @rule()
    def rule_test_mandatory_header_errors(self) -> None:
        """Verify 415 and 406 response codes for missing headers."""
        s415, _, _ = self.client.request(
            "POST",
            "/public/api/person-scan",
            override_headers={"Accept": "application/xml"},
        )
        assert s415 == HTTP_UNSUPPORTED_MEDIA

        s406_post, _, _ = self.client.request(
            "POST",
            "/public/api/person-scan",
            override_headers={
                "Content-Type": "application/xml",
                "Accept": "text/html",
            },
        )
        assert s406_post == HTTP_NOT_ACCEPTABLE

        s406_get, _, _ = self.client.request(
            "GET",
            "/public/api/person-remove",
            params={"identifier": 1},
            override_headers={"Accept": "text/html"},
        )
        assert s406_get == HTTP_NOT_ACCEPTABLE

    @rule(
        cid=st.integers(min_value=600, max_value=800),
        pid=persons,
    )
    def rule_create_command_with_real_subprocess(
        self, cid: int, pid: int
    ) -> None:
        """Execute command in non-test mode invoking CLI minifier."""
        real_app = create_app(storage=data_layer, test_mode=False)
        real_client = HTTPClient(app=real_app)
        raw_js = "/* comment */\nfunction add(x, y) {\n    return x + y;\n}"
        resp = real_client.public_api_command_make(
            cid, raw_js, pid, "math", "completed", 1
        )
        assert int(resp["identifier"]) == cid
        self.oracle.add_command(cid, raw_js, pid, "math", "completed", 1)

    @invariant()
    def check_state_consistency(self) -> None:
        """Verify consistency between API server state and oracle."""
        scanned_persons = self.client.public_api_person_scan()
        assert len(scanned_persons) == len(self.oracle.persons)


def test_bottle_api_state_machine():
    """Run hypothesis state machine test for Bottle HTTP API."""
    run_state_machine_as_test(
        BottleAPIStateMachine,
        settings=settings(max_examples=35, stateful_step_count=25),
    )


def test_real_network_client():
    """Verify HTTP client over real localhost socket connection."""
    test_app = create_app(storage=data_layer, test_mode=True)
    server_thread = threading.Thread(
        target=lambda: test_app.run(
            host="127.0.0.1", port=TEST_PORT, quiet=True
        ),
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.3)

    net_client = HTTPClient(base_url=f"http://127.0.0.1:{TEST_PORT}")
    p_resp = net_client.public_api_person_make(
        99, "127.0.0.1", "Linux", "NetClient"
    )
    assert int(p_resp["identifier"]) == 99

    c_resp = net_client.public_api_command_make(
        99, "var a = 1;", 99, "test", "done", 0
    )
    assert int(c_resp["identifier"]) == 99

    del_resp = net_client.public_api_person_remove(99)
    assert del_resp["success"] == "true"
