from skedule import db

from devtools.common import create_local_app, ensure_instance_path


def main() -> int:
    app = create_local_app()
    ensure_instance_path(app)

    with app.app_context():
        print("Deleting all data...")
        db.drop_all()

        print("Recreating tables...")
        db.create_all()

        table_names = db.inspect(db.engine).get_table_names()
        print(f"Created tables: {', '.join(table_names)}")

    print("Done!")
    return 0
