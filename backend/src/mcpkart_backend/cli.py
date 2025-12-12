"""CLI utilities for MCP Kart backend."""

import argparse
import sys

from mcpkart_backend.db import SessionLocal, RaceResult, RacerResult, User


def reset_db():
    """Delete all data from race-related tables."""
    db = SessionLocal()
    try:
        # Delete in order to respect foreign key constraints
        racer_count = db.query(RacerResult).delete()
        race_count = db.query(RaceResult).delete()
        db.commit()
        print(f"Deleted {racer_count} racer results")
        print(f"Deleted {race_count} race results")
        print("Database reset complete!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def reset_all():
    """Delete ALL data including users."""
    db = SessionLocal()
    try:
        racer_count = db.query(RacerResult).delete()
        race_count = db.query(RaceResult).delete()
        user_count = db.query(User).delete()
        db.commit()
        print(f"Deleted {racer_count} racer results")
        print(f"Deleted {race_count} race results")
        print(f"Deleted {user_count} users")
        print("Full database reset complete!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="MCP Kart CLI utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # reset-db command
    reset_parser = subparsers.add_parser(
        "reset-db",
        help="Delete all race data (keeps users)"
    )
    reset_parser.add_argument(
        "--include-users",
        action="store_true",
        help="Also delete user accounts"
    )

    args = parser.parse_args()

    if args.command == "reset-db":
        if args.include_users:
            reset_all()
        else:
            reset_db()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
