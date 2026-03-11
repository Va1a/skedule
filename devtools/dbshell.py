import os
import sys

from devtools.common import create_local_app, ensure_local_database, get_local_database_path


def main() -> int:
    app = create_local_app()
    ensure_local_database(app)
    database_path = get_local_database_path(app)
    os.execvp("sqlite3", ["sqlite3", str(database_path), *sys.argv[1:]])
    return 0
