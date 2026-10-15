"""Worker entry point: check every active monitor once and save the results."""

import asyncio
import logging
import os
import sys

import psycopg
from dotenv import load_dotenv

import db
from checker import check_url, make_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # skip its per-request log lines
log = logging.getLogger("worker")


async def run_once(conn: psycopg.AsyncConnection) -> None:
    monitors = await db.load_active_monitors(conn)
    log.info("loaded %d active monitors", len(monitors))

    async with make_client() as client:
        results = await asyncio.gather(
            *(check_url(client, m.url, m.timeout_ms, m.expected_status) for m in monitors)
        )

    await db.save_checks(conn, [(m.id, r) for m, r in zip(monitors, results)])

    for m, r in zip(monitors, results):
        if r.success:
            log.info("UP   %s (%s) %d ms", m.name, m.url, r.response_time_ms)
        else:
            log.warning("DOWN %s (%s) %s", m.name, m.url, r.error)


async def main() -> None:
    # Local dev: read ../.env. In Docker/AWS there is no .env file, so this does
    # nothing and the real environment variables are used.
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    database_url = os.environ["DATABASE_URL"]
    async with await psycopg.AsyncConnection.connect(database_url) as conn:
        await run_once(conn)


if __name__ == "__main__":
    # psycopg's async mode can't use Windows' default event loop, so use the
    # selector loop there. In Docker/AWS (Linux) the default loop is used.
    if sys.platform == "win32":
        asyncio.run(main(), loop_factory=asyncio.SelectorEventLoop)
    else:
        asyncio.run(main())
