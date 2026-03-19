from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path = "config/config.yaml") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        fallback_path = config_path.with_name("config.example.yaml")
        if fallback_path.exists():
            config_path = fallback_path
        else:
            raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def build_postgres_dsn(database_config: dict[str, Any]) -> str:
    user = database_config["user"]
    password = database_config["password"]
    host = database_config["host"]
    port = database_config["port"]
    db_name = database_config["name"]
    connect_timeout = database_config.get("connect_timeout")
    dsn = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    if connect_timeout:
        dsn = f"{dsn}?connect_timeout={int(connect_timeout)}"
    return dsn
