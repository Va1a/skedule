import os

from devtools.common import create_local_app, ensure_local_database


def main() -> int:
    app = create_local_app()
    result = ensure_local_database(app)

    host = os.environ.get("SKEDULE_DEV_HOST", "127.0.0.1")
    port = int(os.environ.get("SKEDULE_DEV_PORT", "8080"))

    print(
        "Development database ready: "
        f"{len(result['table_names'])} tables, "
        f"{result['seeded_users']} users seeded this run."
    )
    app.run(debug=True, host=host, port=port)
    return 0
