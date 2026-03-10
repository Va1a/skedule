from pathlib import Path

from skedule import db

from devtools.common import create_local_app


def main() -> int:
    app = create_local_app()
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    with app.app_context():
        print("Deleting all data...")
        db.drop_all()

        print("Recreating tables...")
        db.create_all()

        table_names = db.inspect(db.engine).get_table_names()
        print(f"Created tables: {', '.join(table_names)}")

    print("Done!")
    return 0
