"""Demo script: persist Stage 3 data into a real SQLite file."""

import os
import sys

SRC_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "src"
)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

pony_storage = __import__("pony_storage")
http_client_mod = __import__("http_client")
HTTPClient = http_client_mod.HTTPClient
http_server_mod = __import__("http_server")
create_app = http_server_mod.create_app

DB_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "demo.db"
)
ADD_MODE = "add"
CLEAR_MODE = "clear"
PERSON_ID = 1
COMMAND_ID = 1
FIRST_ARG = 1


def build_client():
    """Initialize SQLite file storage and return configured client."""
    pony_storage.init_database(DB_FILE)
    app = create_app(storage=pony_storage, test_mode=True)
    return HTTPClient(app=app)


def add_demo_data():
    """Insert sample person, command and result into database."""
    client = build_client()
    client.public_api_person_make(
        PERSON_ID, "192.168.1.10", "Windows", "DemoAgent"
    )
    client.public_api_command_make(
        COMMAND_ID,
        "function add(a,b){return a+b;}",
        PERSON_ID,
        "demo",
        "done",
        1,
    )
    print("Inserted person, command and result into " + DB_FILE)


def clear_demo_data():
    """Remove all rows from database tables."""
    build_client()
    pony_storage.clear_all()
    print("Cleared all tables in " + DB_FILE)


def main():
    """Run selected demo mode."""
    total_args = len(sys.argv)
    if total_args > FIRST_ARG:
        if sys.argv[FIRST_ARG] == CLEAR_MODE:
            clear_demo_data()
            return
    add_demo_data()


if __name__ == "__main__":
    main()
