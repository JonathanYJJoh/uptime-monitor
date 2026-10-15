"""Check a single URL once: status code, response time, and SSL certificate expiry."""

import asyncio
import ssl
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx


@dataclass
class CheckResult:
    status_code: int | None  # None when the site never answered
    response_time_ms: int | None
    success: bool
    error: str | None
    ssl_expires_at: datetime | None  # None for http:// or when TLS failed


async def check_url(
    client: httpx.AsyncClient, url: str, timeout_ms: int, expected_status: int
) -> CheckResult:
    start = time.perf_counter()
    try:
        # asyncio.timeout caps the WHOLE check (DNS + connect + TLS + response).
        # httpx's own timeout only applies to each phase separately.
        async with asyncio.timeout(timeout_ms / 1000):
            # stream() returns as soon as the status line and headers arrive,
            # so we time "how fast did the server answer" without downloading the page.
            async with client.stream("GET", url) as response:
                elapsed_ms = round((time.perf_counter() - start) * 1000)
                ssl_expires_at = _ssl_expiry(response)
    except TimeoutError:
        return CheckResult(None, None, False, f"timed out after {timeout_ms} ms", None)
    except httpx.HTTPError as e:
        # Covers DNS failures, refused connections, bad certificates, etc.
        return CheckResult(None, None, False, f"{type(e).__name__}: {e}", None)

    ok = response.status_code == expected_status
    error = None if ok else f"expected status {expected_status}, got {response.status_code}"
    return CheckResult(response.status_code, elapsed_ms, ok, error, ssl_expires_at)


def _ssl_expiry(response: httpx.Response) -> datetime | None:
    """Read the server certificate's expiry date from the open connection."""
    stream = response.extensions.get("network_stream")
    ssl_object = stream.get_extra_info("ssl_object") if stream else None
    cert = ssl_object.getpeercert() if ssl_object else None
    if not cert or "notAfter" not in cert:
        return None
    return datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), tz=timezone.utc)


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        follow_redirects=True,  # e.g. http://site.com -> https://www.site.com
        headers={"User-Agent": "uptime-monitor/0.1"},
    )


async def _main(urls: list[str]) -> None:
    async with make_client() as client:
        start = time.perf_counter()
        # gather() runs every check at the same time and waits for all of them.
        results = await asyncio.gather(*(check_url(client, u, 5000, 200) for u in urls))
        total_ms = round((time.perf_counter() - start) * 1000)

    for url, r in zip(urls, results):
        status = "UP  " if r.success else "DOWN"
        ssl_info = r.ssl_expires_at.date() if r.ssl_expires_at else "-"
        time_info = f"{r.response_time_ms}ms" if r.response_time_ms is not None else "-"
        print(f"{status} {url}\n     status={r.status_code} time={time_info} "
              f"ssl_expires={ssl_info} error={r.error}")
    print(f"\nChecked {len(urls)} URLs concurrently in {total_ms} ms total")


if __name__ == "__main__":
    asyncio.run(_main(sys.argv[1:] or ["https://example.com"]))
