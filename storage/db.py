from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import asdict
from typing import Iterator

from parser.parser import ParsedAd

logger = logging.getLogger(__name__)

try:
    import psycopg
    from psycopg import OperationalError
except ImportError:  # pragma: no cover - dependency may be absent in tests
    psycopg = None
    OperationalError = Exception


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ads_creative (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(20) NOT NULL,
    game_name VARCHAR(100) NOT NULL,
    hook TEXT NOT NULL,
    creative_type VARCHAR(50),
    country VARCHAR(20),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    library_id VARCHAR(50),
    material_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_UNIQUE_INDEX_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS uniq_ads_hook_platform
ON ads_creative(platform, hook);
"""


class InMemoryStorage:
    """Simple storage backend used in tests and local dry runs."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], ParsedAd] = {}

    def init_schema(self) -> None:
        logger.info("in-memory storage initialized")

    def upsert_ad(self, ad: ParsedAd) -> bool:
        key = ad.dedup_key()
        is_new = key not in self._items
        self._items[key] = ad
        return is_new

    def list_ads(self) -> list[ParsedAd]:
        return list(self._items.values())


class PostgresStorage:
    def __init__(self, dsn: str) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg is not installed. Run `pip install -r requirements.txt` first.")
        self.dsn = dsn

    @contextmanager
    def _connect(self) -> Iterator[psycopg.Connection]:
        try:
            connection = psycopg.connect(self.dsn)
        except OperationalError as exc:
            raise RuntimeError(
                "Failed to connect to Postgres. Please confirm the database is running "
                "and config/config.yaml has the correct host, port, database, user, and password."
            ) from exc
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def init_schema(self) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
            cur.execute(CREATE_UNIQUE_INDEX_SQL)
            cur.execute("ALTER TABLE ads_creative ADD COLUMN IF NOT EXISTS library_id VARCHAR(50)")
            cur.execute("ALTER TABLE ads_creative ADD COLUMN IF NOT EXISTS material_url TEXT")

    def upsert_ad(self, ad: ParsedAd) -> bool:
        payload = asdict(ad)
        sql = """
        INSERT INTO ads_creative (
            platform, game_name, hook, creative_type, country, first_seen, last_seen, library_id, material_url
        ) VALUES (
            %(platform)s, %(game_name)s, %(hook)s, %(creative_type)s, %(country)s, %(first_seen)s, %(last_seen)s,
            %(library_id)s, %(material_url)s
        )
        ON CONFLICT (platform, hook) DO UPDATE SET
            game_name = EXCLUDED.game_name,
            creative_type = EXCLUDED.creative_type,
            country = EXCLUDED.country,
            first_seen = COALESCE(ads_creative.first_seen, EXCLUDED.first_seen),
            last_seen = GREATEST(ads_creative.last_seen, EXCLUDED.last_seen),
            library_id = COALESCE(EXCLUDED.library_id, ads_creative.library_id),
            material_url = COALESCE(EXCLUDED.material_url, ads_creative.material_url)
        RETURNING (xmax = 0) AS inserted;
        """
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(sql, payload)
            result = cur.fetchone()
        return bool(result[0]) if result else False
