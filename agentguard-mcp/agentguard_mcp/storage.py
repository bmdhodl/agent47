"""SQLite budget storage for the AgentGuard MCP server."""

from __future__ import annotations

import os
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, TypedDict

Period = Literal["session", "day", "month"]

VALID_PERIODS: set[str] = {"session", "day", "month"}


class BudgetSnapshot(TypedDict):
    scope: str
    tokens_used: int
    tokens_limit: int | None
    usd_used: float
    usd_limit: float | None
    period: Period
    period_resets_at: str | None
    kill_switch: bool


class RecordResult(TypedDict):
    allowed: bool
    reasons: list[str]
    scopes_checked: list[str]


@dataclass(frozen=True)
class Budget:
    scope: str
    limit_tokens: int | None
    limit_usd: float | None
    period: Period
    kill_switch: bool


def default_db_path() -> Path:
    configured = os.environ.get("AGENTGUARD_DB_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".agentguard" / "state.db"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def period_start(period: Period, now: datetime) -> datetime:
    current = now.astimezone(timezone.utc)
    if period == "session":
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if period == "day":
        return current.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unsupported period: {period}")


def period_reset(period: Period, now: datetime) -> datetime | None:
    current = now.astimezone(timezone.utc)
    if period == "session":
        return None
    if period == "day":
        start = period_start("day", current)
        return start + timedelta(days=1)
    if period == "month":
        start = period_start("month", current)
        if start.month == 12:
            return start.replace(year=start.year + 1, month=1)
        return start.replace(month=start.month + 1)
    raise ValueError(f"Unsupported period: {period}")


def validate_period(period: str) -> Period:
    if period not in VALID_PERIODS:
        raise ValueError("period must be one of: session, day, month")
    return period  # type: ignore[return-value]


def validate_limits(limit_tokens: int | None, limit_usd: float | None) -> None:
    if limit_tokens is None and limit_usd is None:
        raise ValueError("set at least one of limit_tokens or limit_usd")
    if limit_tokens is not None and limit_tokens < 0:
        raise ValueError("limit_tokens must be non-negative")
    if limit_usd is not None and limit_usd < 0:
        raise ValueError("limit_usd must be non-negative")


class BudgetStore:
    """Local SQLite store for MCP budget definitions and usage events."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path).expanduser() if db_path is not None else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def set_budget(
        self,
        scope: str,
        limit_tokens: int | None,
        limit_usd: float | None,
        period: str,
    ) -> BudgetSnapshot:
        scope = normalize_scope(scope)
        typed_period = validate_period(period)
        validate_limits(limit_tokens, limit_usd)
        now = utc_now()
        with self._lock, self._connection() as conn:
            conn.execute(
                """
                    INSERT INTO budgets (
                        scope, limit_tokens, limit_usd, period, kill_switch, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                    ON CONFLICT(scope) DO UPDATE SET
                        limit_tokens = excluded.limit_tokens,
                        limit_usd = excluded.limit_usd,
                        period = excluded.period,
                        updated_at = excluded.updated_at
                    """,
                (
                    scope,
                    limit_tokens,
                    limit_usd,
                    typed_period,
                    format_utc(now),
                    format_utc(now),
                ),
            )
        return self.check_remaining(scope)

    def kill_switch(self, scope: str, enable: bool = True) -> BudgetSnapshot:
        scope = normalize_scope(scope)
        now = format_utc(utc_now())
        with self._lock, self._connection() as conn:
            existing = conn.execute("SELECT scope FROM budgets WHERE scope = ?", (scope,)).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO budgets (
                        scope, limit_tokens, limit_usd, period, kill_switch, created_at, updated_at
                    )
                    VALUES (?, NULL, NULL, 'session', ?, ?, ?)
                    """,
                    (scope, int(enable), now, now),
                )
            else:
                conn.execute(
                    "UPDATE budgets SET kill_switch = ?, updated_at = ? WHERE scope = ?",
                    (int(enable), now, scope),
                )
        return self.check_remaining(scope)

    def check_remaining(self, scope: str, now: datetime | None = None) -> BudgetSnapshot:
        scope = normalize_scope(scope)
        current = now or utc_now()
        budget = self._get_budget(scope)
        if budget is None:
            budget = Budget(scope, None, None, "session", False)
        tokens_used, usd_used = self._usage_for(scope, budget.period, current)
        reset = period_reset(budget.period, current)
        return {
            "scope": scope,
            "tokens_used": tokens_used,
            "tokens_limit": budget.limit_tokens,
            "usd_used": usd_used,
            "usd_limit": budget.limit_usd,
            "period": budget.period,
            "period_resets_at": format_utc(reset) if reset is not None else None,
            "kill_switch": budget.kill_switch,
        }

    def record_call(
        self,
        server: str,
        tool: str,
        tokens_in: int,
        tokens_out: int,
        cost_usd: float,
        session_id: str | None = None,
        now: datetime | None = None,
    ) -> RecordResult:
        if tokens_in < 0 or tokens_out < 0:
            raise ValueError("tokens_in and tokens_out must be non-negative")
        if cost_usd < 0:
            raise ValueError("cost_usd must be non-negative")

        current = now or utc_now()
        scopes = matching_scopes(server, tool, session_id)
        configured = [budget for budget in self._get_budgets(scopes) if budget is not None]
        kill_reasons = [
            f"{budget.scope} is blocked by kill_switch" for budget in configured if budget.kill_switch
        ]
        if kill_reasons:
            return {"allowed": False, "reasons": kill_reasons, "scopes_checked": scopes}

        reasons = self._budget_exceeded_reasons(configured, tokens_in + tokens_out, cost_usd, current)
        if reasons:
            return {"allowed": False, "reasons": reasons, "scopes_checked": scopes}

        timestamp = format_utc(current)
        with self._lock, self._connection() as conn:
            conn.executemany(
                """
                    INSERT INTO usage_events (
                        ts, scope, server, tool, session_id, tokens_in, tokens_out, cost_usd
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                [
                    (timestamp, scope, server, tool, session_id, tokens_in, tokens_out, cost_usd)
                    for scope in scopes
                ],
            )

        return {"allowed": True, "reasons": [], "scopes_checked": scopes}

    def _budget_exceeded_reasons(
        self,
        budgets: list[Budget],
        added_tokens: int,
        added_cost_usd: float,
        now: datetime,
    ) -> list[str]:
        reasons: list[str] = []
        for budget in budgets:
            snapshot = self.check_remaining(budget.scope, now)
            projected_tokens = snapshot["tokens_used"] + added_tokens
            projected_usd = snapshot["usd_used"] + added_cost_usd
            if snapshot["tokens_limit"] is not None and projected_tokens > snapshot["tokens_limit"]:
                reasons.append(
                    f"{budget.scope} token budget exceeded: "
                    f"{projected_tokens} > {snapshot['tokens_limit']}"
                )
            if snapshot["usd_limit"] is not None and projected_usd > snapshot["usd_limit"]:
                reasons.append(
                    f"{budget.scope} dollar budget exceeded: "
                    f"{projected_usd:.6f} > {snapshot['usd_limit']:.6f}"
                )
        return reasons

    def list_budgets(self, now: datetime | None = None) -> list[BudgetSnapshot]:
        current = now or utc_now()
        with self._connection() as conn:
            rows = conn.execute("SELECT scope FROM budgets ORDER BY scope").fetchall()
        return [self.check_remaining(str(row["scope"]), current) for row in rows]

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS budgets (
                    scope TEXT PRIMARY KEY,
                    limit_tokens INTEGER,
                    limit_usd REAL,
                    period TEXT NOT NULL,
                    kill_switch INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    server TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    session_id TEXT,
                    tokens_in INTEGER NOT NULL,
                    tokens_out INTEGER NOT NULL,
                    cost_usd REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_usage_scope_ts ON usage_events(scope, ts);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _get_budget(self, scope: str) -> Budget | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT scope, limit_tokens, limit_usd, period, kill_switch FROM budgets WHERE scope = ?",
                (scope,),
            ).fetchone()
        if row is None:
            return None
        return Budget(
            scope=str(row["scope"]),
            limit_tokens=row["limit_tokens"],
            limit_usd=row["limit_usd"],
            period=validate_period(str(row["period"])),
            kill_switch=bool(row["kill_switch"]),
        )

    def _get_budgets(self, scopes: list[str]) -> list[Budget | None]:
        return [self._get_budget(scope) for scope in scopes]

    def _usage_for(self, scope: str, period: Period, now: datetime) -> tuple[int, float]:
        since = format_utc(period_start(period, now))
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(tokens_in + tokens_out), 0) AS tokens_used,
                    COALESCE(SUM(cost_usd), 0.0) AS usd_used
                FROM usage_events
                WHERE scope = ? AND ts >= ?
                """,
                (scope, since),
            ).fetchone()
        return int(row["tokens_used"]), float(row["usd_used"])


def normalize_scope(scope: str) -> str:
    normalized = scope.strip()
    if not normalized:
        raise ValueError("scope must not be empty")
    return normalized


def matching_scopes(server: str, tool: str, session_id: str | None) -> list[str]:
    server_name = server.strip()
    tool_name = tool.strip()
    if not server_name:
        raise ValueError("server must not be empty")
    if not tool_name:
        raise ValueError("tool must not be empty")

    scopes = ["global", f"server:{server_name}", f"tool:{server_name}.{tool_name}"]
    if session_id is not None and session_id.strip():
        scopes.append(f"session:{session_id.strip()}")
    return scopes
