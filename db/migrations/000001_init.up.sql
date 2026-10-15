-- Migration 000001: create the initial tables (monitors, checks, incidents)

-- The websites we watch.
CREATE TABLE monitors (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name             TEXT        NOT NULL,
    url              TEXT        NOT NULL CHECK (url ~ '^https?://'),
    interval_seconds INTEGER     NOT NULL DEFAULT 60    CHECK (interval_seconds BETWEEN 30 AND 86400),
    timeout_ms       INTEGER     NOT NULL DEFAULT 10000 CHECK (timeout_ms BETWEEN 100 AND 60000),
    expected_status  INTEGER     NOT NULL DEFAULT 200   CHECK (expected_status BETWEEN 100 AND 599),
    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per visit the worker makes.
CREATE TABLE checks (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    monitor_id       BIGINT      NOT NULL REFERENCES monitors (id) ON DELETE CASCADE,
    checked_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    status_code      INTEGER,          -- NULL when no response at all (DNS failure, timeout, refused)
    response_time_ms INTEGER,          -- NULL when no response
    success          BOOLEAN     NOT NULL,
    error            TEXT,             -- NULL on success
    ssl_expires_at   TIMESTAMPTZ       -- NULL for http:// sites or when the TLS handshake failed
);

-- "Latest checks for monitor X, newest first" (dashboard, uptime %, 3-failure rule).
CREATE INDEX checks_monitor_id_checked_at_idx ON checks (monitor_id, checked_at DESC);

-- "Delete checks older than 30 days" (retention job).
CREATE INDEX checks_checked_at_idx ON checks (checked_at);

-- Outages. An incident is open while resolved_at IS NULL.
CREATE TABLE incidents (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    monitor_id  BIGINT      NOT NULL REFERENCES monitors (id) ON DELETE CASCADE,
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    cause       TEXT,
    CHECK (resolved_at IS NULL OR resolved_at >= started_at)
);

-- Incident history per monitor, newest first.
CREATE INDEX incidents_monitor_id_started_at_idx ON incidents (monitor_id, started_at DESC);

-- At most ONE open incident per monitor, enforced by the database itself.
CREATE UNIQUE INDEX incidents_one_open_per_monitor_idx ON incidents (monitor_id) WHERE resolved_at IS NULL;
