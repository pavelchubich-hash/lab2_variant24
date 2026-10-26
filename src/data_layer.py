"""In-memory data layer implementing ER schema for Variant 24."""

import time

TIME_WINDOW_SECONDS = 300
NOT_FOUND_INDEX = -1
EMPTY_COUNT = 0

persons = []
commands = []
results = []


def clear_all() -> None:
    """Clear all records from in-memory stores."""
    persons.clear()
    commands.clear()
    results.clear()


def create_person(
    identifier: int,
    ip: str,
    platform: str,
    user_agent: str,
    created: int = None,
) -> int:
    """Create or update a person record and store as tuple."""
    if created is None:
        created = int(time.time())
    record = (identifier, created, ip, platform, user_agent)
    for idx, item in enumerate(persons):
        if item[0] == identifier:
            persons[idx] = record
            return identifier
    persons.append(record)
    return identifier


def delete_person(identifier: int) -> bool:
    """Delete person record matching identifier."""
    idx_to_remove = NOT_FOUND_INDEX
    for idx, item in enumerate(persons):
        if item[0] == identifier:
            idx_to_remove = idx
            break
    if idx_to_remove != NOT_FOUND_INDEX:
        persons.pop(idx_to_remove)
        return True
    return False


def get_persons() -> list:
    """Return all stored person records."""
    return list(persons)


def create_command(
    identifier: int,
    data: str,
    person: int,
    tags: str,
    status: str,
    triggered: int,
    created: int = None,
) -> int:
    """Create or update a command record and store as tuple."""
    if created is None:
        created = int(time.time())
    record = (identifier, created, data, person, tags, status, triggered)
    for idx, item in enumerate(commands):
        if item[0] == identifier:
            commands[idx] = record
            return identifier
    commands.append(record)
    return identifier


def delete_command(identifier: int) -> bool:
    """Delete command record matching identifier."""
    idx_to_remove = NOT_FOUND_INDEX
    for idx, item in enumerate(commands):
        if item[0] == identifier:
            idx_to_remove = idx
            break
    if idx_to_remove != NOT_FOUND_INDEX:
        commands.pop(idx_to_remove)
        return True
    return False


def get_commands_by_person(person: int) -> list:
    """Return command records belonging to a specific person."""
    return [cmd for cmd in commands if cmd[3] == person]


def get_all_commands() -> list:
    """Return all stored command records."""
    return list(commands)


def create_result(
    identifier: int,
    result: str,
    status: str,
    exception: str,
    command: int,
    created: int = None,
) -> int:
    """Create or update a result record and store as tuple."""
    if created is None:
        created = int(time.time())
    record = (identifier, created, result, status, exception, command)
    for idx, item in enumerate(results):
        if item[0] == identifier:
            results[idx] = record
            return identifier
    results.append(record)
    return identifier


def get_results_by_command(command: int) -> list:
    """Return result records linked to a specific command."""
    return [res for res in results if res[5] == command]


def get_all_results() -> list:
    """Return all stored result records."""
    return list(results)


def _find_command_tags(cmd_id: int) -> str:
    """Find tags of a command by identifier."""
    for cmd in commands:
        if cmd[0] == cmd_id:
            return cmd[4]
    return ""


def select_report_data() -> list:
    """Select command tags and result values according to formula 24."""
    threshold = int(time.time()) - TIME_WINDOW_SECONDS
    valid_results = [res for res in results if res[1] > threshold]
    report_items = []
    for res in valid_results:
        tags = _find_command_tags(res[5])
        report_items.append((tags, res[2]))
    return report_items
