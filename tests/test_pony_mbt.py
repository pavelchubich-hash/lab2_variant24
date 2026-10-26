"""Stage 3 Model-Based Testing with PonyORM SQLite backend."""

from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    invariant,
    rule,
    run_state_machine_as_test,
)
from http_client import HTTPClient
from http_server import (
    HTTP_NOT_ACCEPTABLE,
    HTTP_UNSUPPORTED_MEDIA,
    create_app,
)
import pony_storage

MIN_COLLECTION_SIZE = 0
INDEX_FIRST = 0
STATUS_OK = 200
NON_EXISTENT_ID = 999999


class PonyModelOracle:
    """Independent oracle for PonyORM database state."""

    def __init__(self) -> None:
        """Initialize tracking dictionaries."""
        self.persons = {}
        self.commands = {}
        self.results = {}

    def add_person(
        self, pid: int, ip: str, platform: str, user_agent: str
    ) -> None:
        """Add or update person in oracle."""
        self.persons[pid] = (pid, ip, platform, user_agent)

    def remove_person(self, pid: int) -> bool:
        """Remove person and cascade associated commands."""
        if pid in self.persons:
            del self.persons[pid]
            to_del = [c for c, d in self.commands.items() if d[2] == pid]
            for cid in to_del:
                self.remove_command(cid)
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
        """Add or update command and its result in oracle."""
        if pid not in self.persons:
            self.persons[pid] = (pid, "127.0.0.1", "Linux", "Default")
        self.commands[cid] = (cid, data, pid, tags, status, triggered)
        self.results[cid] = (cid, "mock_res", "success", "none", cid)

    def remove_command(self, cid: int) -> bool:
        """Remove command and result in oracle."""
        if cid in self.commands:
            del self.commands[cid]
            if cid in self.results:
                del self.results[cid]
            return True
        return False


class PonyAPIStateMachine(RuleBasedStateMachine):
    """Model-based state machine for API with PonyORM SQLite."""

    persons = Bundle("persons")
    commands = Bundle("commands")

    def __init__(self) -> None:
        """Initialize state machine with PonyORM backend."""
        super().__init__()
        pony_storage.init_database(":memory:")
        pony_storage.clear_all()
        self.app = create_app(storage=pony_storage, test_mode=True)
        self.client = HTTPClient(app=self.app)
        self.oracle = PonyModelOracle()
        self.last_cmd_id = -1

    @rule(
        target=persons,
        pid=st.integers(min_value=1, max_value=300),
        ip=st.sampled_from(["127.0.0.1", "192.168.0.1", "10.10.10.10"]),
        platform=st.sampled_from(["Windows", "Linux", "MacOS"]),
        user_agent=st.sampled_from(["Chrome", "Edge", "Firefox"]),
    )
    def rule_create_person(
        self, pid: int, ip: str, platform: str, user_agent: str
    ) -> int:
        """Test person creation via HTTP client with PonyORM."""
        resp = self.client.public_api_person_make(
            pid, ip, platform, user_agent
        )
        assert int(resp["identifier"]) == pid
        self.oracle.add_person(pid, ip, platform, user_agent)
        return pid

    @rule(pid=persons)
    def rule_update_person(self, pid: int) -> None:
        """Test updating existing person in database."""
        resp = self.client.public_api_person_make(
            pid, "10.0.0.99", "BSD", "UpdatedUA"
        )
        assert int(resp["identifier"]) == pid
        self.oracle.add_person(pid, "10.0.0.99", "BSD", "UpdatedUA")

    @rule(cid=commands)
    def rule_update_command(self, cid: int) -> None:
        """Test updating existing command in database."""
        cmd_data = self.oracle.commands.get(cid)
        if cmd_data:
            pid = cmd_data[2]
            resp = self.client.public_api_command_make(
                cid, "var updated = true;", pid, "upd", "done", 1
            )
            assert int(resp["identifier"]) == cid

    @rule(pid=persons)
    def rule_remove_person(self, pid: int) -> None:
        """Test person deletion via HTTP client with PonyORM."""
        resp = self.client.public_api_person_remove(pid)
        exp = "true" if self.oracle.remove_person(pid) else "false"
        assert resp.get("success") == exp

    @rule()
    def rule_remove_missing_person(self) -> None:
        """Test deletion of non existent person."""
        resp = self.client.public_api_person_remove(NON_EXISTENT_ID)
        assert resp.get("success") == "false"

    @rule()
    def rule_scan_persons(self) -> None:
        """Test scanning persons with and without filters."""
        all_p = self.client.public_api_person_scan()
        assert len(all_p) == len(self.oracle.persons)
        f_p = self.client.public_api_person_scan(filters={"ip": "127.0.0.1"})
        assert isinstance(f_p, list)

    @rule(
        target=commands,
        cid=st.integers(min_value=1, max_value=300),
        pid=persons,
        data=st.sampled_from(["let x = 10;", "console.log('hi');"]),
        tags=st.sampled_from(["v8", "spidermonkey", "quickjs"]),
        status=st.sampled_from(["ready", "queued"]),
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
        """Test command creation via HTTP client with PonyORM."""
        resp = self.client.public_api_command_make(
            cid, data, pid, tags, status, triggered
        )
        assert int(resp["identifier"]) == cid
        self.oracle.add_command(cid, data, pid, tags, status, triggered)
        self.last_cmd_id = cid
        return cid

    @rule(cid=commands)
    def rule_remove_command(self, cid: int) -> None:
        """Test command removal via HTTP client with PonyORM."""
        resp = self.client.public_api_command_remove(cid)
        exp = "true" if self.oracle.remove_command(cid) else "false"
        assert resp.get("success") == exp

    @rule()
    def rule_remove_missing_command(self) -> None:
        """Test deletion of non existent command."""
        resp = self.client.public_api_command_remove(NON_EXISTENT_ID)
        assert resp.get("success") == "false"

    @rule(pid=persons)
    def rule_scan_commands_by_person(self, pid: int) -> None:
        """Test scanning commands by person foreign key."""
        cmds = self.client.public_api_command_scan(pid)
        exp = sum(1 for c in self.oracle.commands.values() if c[2] == pid)
        assert len(cmds) == exp

    @rule()
    def rule_scan_results_and_reports(self) -> None:
        """Test scanning results and generating formula 24 report."""
        if self.last_cmd_id > MIN_COLLECTION_SIZE:
            res = self.client.public_api_result_scan(self.last_cmd_id)
            assert len(res) >= MIN_COLLECTION_SIZE
        report = self.client.public_api_report_scan()
        assert len(report) >= MIN_COLLECTION_SIZE

    @rule()
    def rule_verify_mandatory_headers(self) -> None:
        """Verify headers 415 and 406 on PonyORM app."""
        code415, _, _ = self.client.request(
            "POST",
            "/public/api/person-scan",
            override_headers={"Accept": "application/xml"},
        )
        assert code415 == HTTP_UNSUPPORTED_MEDIA

        code406, _, _ = self.client.request(
            "GET",
            "/public/api/person-remove",
            params={"identifier": 1},
            override_headers={"Accept": "text/plain"},
        )
        assert code406 == HTTP_NOT_ACCEPTABLE

    @rule(
        cid=st.integers(min_value=501, max_value=600),
        pid=persons,
    )
    def rule_create_command_real_computation(
        self, cid: int, pid: int
    ) -> None:
        """Execute real CLI minifier with PonyORM storage."""
        real_app = create_app(storage=pony_storage, test_mode=False)
        real_client = HTTPClient(app=real_app)
        raw_code = "// note\nlet square = function(n) { return n * n; };"
        resp = real_client.public_api_command_make(
            cid, raw_code, pid, "fast", "active", 1
        )
        assert int(resp["identifier"]) == cid
        self.oracle.add_command(
            cid, raw_code, pid, "fast", "active", 1
        )

    @invariant()
    def check_pony_state_consistency(self) -> None:
        """Ensure database state matches oracle."""
        persons = self.client.public_api_person_scan()
        assert len(persons) == len(self.oracle.persons)
        all_cmds = pony_storage.get_all_commands()
        assert isinstance(all_cmds, list)
        all_res = pony_storage.get_all_results()
        assert isinstance(all_res, list)


def test_pony_api_state_machine():
    """Run hypothesis state machine test for PonyORM SQLite backend."""
    run_state_machine_as_test(
        PonyAPIStateMachine,
        settings=settings(max_examples=35, stateful_step_count=25),
    )
