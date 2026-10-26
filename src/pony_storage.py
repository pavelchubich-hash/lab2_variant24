"""SQLite data access layer using PonyORM for Stage 3."""

import time
from pony.orm import Database, PrimaryKey, Required, Set, db_session, select

TIME_WINDOW_SECONDS = 300

db = Database()


class Person(db.Entity):
    """Person entity representing client session identity."""

    _table_ = "person"
    identifier = PrimaryKey(int)
    created = Required(int)
    ip = Required(str)
    platform = Required(str)
    user_agent = Required(str)
    commands = Set("Command")


class Command(db.Entity):
    """Command entity storing computation requests."""

    _table_ = "command"
    identifier = PrimaryKey(int)
    created = Required(int)
    data = Required(str)
    person = Required(Person)
    tags = Required(str)
    status = Required(str)
    triggered = Required(int)
    results = Set("Result")


class Result(db.Entity):
    """Result entity containing computation output."""

    _table_ = "result"
    identifier = PrimaryKey(int)
    created = Required(int)
    result = Required(str)
    status = Required(str)
    exception = Required(str)
    command = Required(Command)


def init_database(filename: str = ":memory:") -> None:
    """Bind database to SQLite provider and generate table mapping."""
    if db.provider is None:
        db.bind(provider="sqlite", filename=filename, create_db=True)
        db.generate_mapping(create_tables=True)


@db_session
def clear_all() -> None:
    """Remove all records from database tables."""
    Result.select().delete(bulk=True)
    Command.select().delete(bulk=True)
    Person.select().delete(bulk=True)


@db_session
def create_person(
    identifier: int,
    ip: str,
    platform: str,
    user_agent: str,
    created: int = None,
) -> int:
    """Create or update a person record in database."""
    if created is None:
        created = int(time.time())
    p = Person.get(identifier=identifier)
    if p:
        p.ip = ip
        p.platform = platform
        p.user_agent = user_agent
        p.created = created
    else:
        Person(
            identifier=identifier,
            created=created,
            ip=ip,
            platform=platform,
            user_agent=user_agent,
        )
    return identifier


@db_session
def delete_person(identifier: int) -> bool:
    """Delete a person and cascaded entities by identifier."""
    p = Person.get(identifier=identifier)
    if p:
        for cmd in list(p.commands):
            for res in list(cmd.results):
                res.delete()
            cmd.delete()
        p.delete()
        return True
    return False


@db_session
def get_persons() -> list:
    """Retrieve all persons converted to tuples."""
    persons = select(p for p in Person).order_by(Person.identifier)[:]
    return [
        (p.identifier, p.created, p.ip, p.platform, p.user_agent)
        for p in persons
    ]


@db_session
def create_command(
    identifier: int,
    data: str,
    person: int,
    tags: str,
    status: str,
    triggered: int,
    created: int = None,
) -> int:
    """Create or update a command record in database."""
    if created is None:
        created = int(time.time())
    p = Person.get(identifier=person)
    if not p:
        p = Person(
            identifier=person,
            created=created,
            ip="127.0.0.1",
            platform="Linux",
            user_agent="Default",
        )
    cmd = Command.get(identifier=identifier)
    if cmd:
        cmd.data = data
        cmd.person = p
        cmd.tags = tags
        cmd.status = status
        cmd.triggered = triggered
        cmd.created = created
    else:
        Command(
            identifier=identifier,
            created=created,
            data=data,
            person=p,
            tags=tags,
            status=status,
            triggered=triggered,
        )
    return identifier


@db_session
def delete_command(identifier: int) -> bool:
    """Delete a command and its results by identifier."""
    cmd = Command.get(identifier=identifier)
    if cmd:
        for res in list(cmd.results):
            res.delete()
        cmd.delete()
        return True
    return False


@db_session
def get_commands_by_person(person: int) -> list:
    """Retrieve commands associated with a given person."""
    cmds = select(c for c in Command if c.person.identifier == person)[:]
    return [
        (
            c.identifier,
            c.created,
            c.data,
            c.person.identifier,
            c.tags,
            c.status,
            c.triggered,
        )
        for c in cmds
    ]


@db_session
def get_all_commands() -> list:
    """Retrieve all command records."""
    cmds = select(c for c in Command)[:]
    return [
        (
            c.identifier,
            c.created,
            c.data,
            c.person.identifier,
            c.tags,
            c.status,
            c.triggered,
        )
        for c in cmds
    ]


def _ensure_command_exists(command_id: int, created: int) -> Command:
    """Ensure parent command entity exists or create default one."""
    cmd = Command.get(identifier=command_id)
    if not cmd:
        p = Person.get(identifier=1)
        if not p:
            p = Person(
                identifier=1,
                created=created,
                ip="127.0.0.1",
                platform="Linux",
                user_agent="Default",
            )
        cmd = Command(
            identifier=command_id,
            created=created,
            data="",
            person=p,
            tags="",
            status="pending",
            triggered=0,
        )
    return cmd


@db_session
def create_result(
    identifier: int,
    result: str,
    status: str,
    exception: str,
    command: int,
    created: int = None,
) -> int:
    """Create or update a result record in database."""
    if created is None:
        created = int(time.time())
    cmd = _ensure_command_exists(command, created)
    res = Result.get(identifier=identifier)
    if res:
        res.result = result
        res.status = status
        res.exception = exception
        res.command = cmd
        res.created = created
    else:
        Result(
            identifier=identifier,
            created=created,
            result=result,
            status=status,
            exception=exception,
            command=cmd,
        )
    return identifier


@db_session
def get_results_by_command(command: int) -> list:
    """Retrieve result records associated with a command."""
    results = select(r for r in Result if r.command.identifier == command)[:]
    return [
        (
            r.identifier,
            r.created,
            r.result,
            r.status,
            r.exception,
            r.command.identifier,
        )
        for r in results
    ]


@db_session
def get_all_results() -> list:
    """Retrieve all result records."""
    results = select(r for r in Result)[:]
    return [
        (
            r.identifier,
            r.created,
            r.result,
            r.status,
            r.exception,
            r.command.identifier,
        )
        for r in results
    ]


@db_session
def select_report_data() -> list:
    """Execute join and projection according to formula 24."""
    threshold = int(time.time()) - TIME_WINDOW_SECONDS
    results = select(r for r in Result if r.created > threshold)[:]
    return [(r.command.tags, r.result) for r in results]
