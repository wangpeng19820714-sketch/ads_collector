from __future__ import annotations

import sys

import psycopg
from psycopg import OperationalError, sql

from app.config import load_config


def main() -> int:
    config = load_config()
    database = config["database"]

    host = database["host"]
    port = database["port"]
    user = database["user"]
    password = database["password"]
    target_db = database["name"]
    connect_timeout = int(database.get("connect_timeout", 5))

    admin_dsn = (
        f"postgresql://{user}:{password}@{host}:{port}/postgres"
        f"?connect_timeout={connect_timeout}"
    )

    try:
        with psycopg.connect(admin_dsn, autocommit=True) as conn, conn.cursor() as cur:
            print(f"[INFO] Connected to Postgres as `{user}` on {host}:{port}.")
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
            exists = cur.fetchone() is not None

            if exists:
                print(f"[INFO] Database `{target_db}` already exists.")
            else:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
                print(f"[INFO] Database `{target_db}` created successfully.")
    except OperationalError as exc:
        print("[ERROR] Failed to connect to PostgreSQL with the current config.", file=sys.stderr)
        print(f"        host={host} port={port} user={user} database=postgres", file=sys.stderr)
        print(f"Details: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[ERROR] Failed to initialize database `{target_db}`: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
