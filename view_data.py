from __future__ import annotations

import argparse
import sys

import psycopg
from psycopg import OperationalError

from app.config import build_postgres_dsn, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="View latest ads from Postgres")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--connect-timeout", type=int, default=5)
    return parser.parse_args()


def format_value(value) -> str:
    if value is None:
        return "NULL"
    text = str(value).replace("\n", " ").strip()
    if len(text) > 80:
        return text[:77] + "..."
    return text


def main() -> None:
    args = parse_args()
    config = load_config()
    dsn = build_postgres_dsn(config["database"])

    query = """
    SELECT id, platform, game_name, hook, country, first_seen, last_seen, created_at
    FROM ads_creative
    ORDER BY id DESC
    LIMIT %s
    """

    try:
        with psycopg.connect(dsn, connect_timeout=args.connect_timeout) as conn, conn.cursor() as cur:
            cur.execute(query, (args.limit,))
            rows = cur.fetchall()
    except OperationalError as exc:
        db_config = config["database"]
        print(
            f"[ERROR] Failed to connect to Postgres at "
            f"{db_config['host']}:{db_config['port']}/{db_config['name']}.",
            file=sys.stderr,
        )
        print(f"Details: {exc}", file=sys.stderr)
        print("Please confirm Postgres is running and the config values are correct.", file=sys.stderr)
        sys.exit(1)

    if not rows:
        print("No data found in ads_creative.")
        return

    headers = ["id", "platform", "game_name", "hook", "country", "first_seen", "last_seen", "created_at"]
    formatted_rows = [[format_value(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]

    for row in formatted_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def render_row(values: list[str]) -> str:
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(values))

    print(render_row(headers))
    print("-+-".join("-" * width for width in widths))
    for row in formatted_rows:
        print(render_row(row))


if __name__ == "__main__":
    main()
