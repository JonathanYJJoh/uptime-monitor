"""All of the worker's SQL lives here."""

from dataclasses import dataclass

import psycopg
from psycopg.rows import class_row

from checker import CheckResult


@dataclass
class Monitor:
    id: int
    name: str
    url: str
    interval_seconds: int
    timeout_ms: int
    expected_status: int


async def load_active_monitors(conn: psycopg.AsyncConnection) -> list[Monitor]:
    # class_row turns each row into a Monitor (column names must match field names).
    async with conn.cursor(row_factory=class_row(Monitor)) as cur:
        await cur.execute(
            """
            SELECT id, name, url, interval_seconds, timeout_ms, expected_status
            FROM monitors
            WHERE is_active
            ORDER BY id
            """
        )
        return await cur.fetchall()


async def save_checks(
    conn: psycopg.AsyncConnection, results: list[tuple[int, CheckResult]]
) -> None:
    """Insert one row per (monitor_id, result) in a single transaction."""
    async with conn.transaction():
        async with conn.cursor() as cur:
            # %s placeholders: psycopg sends values separately from the SQL,
            # so a URL or error message can never be executed as SQL (no SQL injection).
            await cur.executemany(
                """
                INSERT INTO checks
                    (monitor_id, checked_at, status_code, response_time_ms, success, error, ssl_expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (monitor_id, r.checked_at, r.status_code, r.response_time_ms,
                     r.success, r.error, r.ssl_expires_at)
                    for monitor_id, r in results
                ],
            )
