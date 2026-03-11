from devtools.common import create_local_app, ensure_local_database


def main() -> int:
    app = create_local_app()
    result = ensure_local_database(app)

    print(
        "Inserted "
        f"{result['seeded_users']} development users and "
        f"{result['seeded_templates']} templates. Default password: test"
    )
    return 0
