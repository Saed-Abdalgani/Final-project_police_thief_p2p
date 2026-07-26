"""Durable daily and named-session quota counters."""

import json
from threading import RLock
from typing import TypedDict

from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.shared.canonical_json import canonical_json_bytes


class _QuotaDocument(TypedDict):
    utc_date: str
    daily: dict[str, int]
    sessions: dict[str, dict[str, int]]


class DurableQuotaManager:
    """Atomically count requests with UTC-day and explicit-session resets."""

    __slots__ = ("_clock", "_lock", "_repository", "_session_id")

    def __init__(
        self,
        repository: RepositoryPort,
        clock: ClockPort,
        *,
        session_id: str,
    ) -> None:
        """Bind durable counters to a validated named process session."""
        if not session_id.isascii() or not session_id.replace("-", "").isalnum():
            raise ValueError("quota session ID is unsafe")
        self._repository = repository
        self._clock = clock
        self._session_id = session_id
        self._lock = RLock()

    def consume(self, service: str, *, daily_limit: int, session_limit: int) -> bool:
        """Consume one unit or leave counters unchanged when exhausted."""
        with self._lock:
            document = self._load()
            today = self._clock.utc_now().date().isoformat()
            if document["utc_date"] != today:
                document = {"utc_date": today, "daily": {}, "sessions": {}}
            daily = document["daily"]
            sessions = document["sessions"]
            session = sessions.setdefault(self._session_id, {})
            if daily.get(service, 0) >= daily_limit or session.get(service, 0) >= session_limit:
                return False
            daily[service] = daily.get(service, 0) + 1
            session[service] = session.get(service, 0) + 1
            self._repository.save("gatekeeper-quota", canonical_json_bytes(document))
            return True

    def reset_session(self, *, confirmed: bool) -> None:
        """Perform an explicit safe reset for the current named session only."""
        if not confirmed:
            raise ValueError("quota reset requires operator confirmation")
        with self._lock:
            document = self._load()
            document["sessions"].pop(self._session_id, None)
            self._repository.save("gatekeeper-quota", canonical_json_bytes(document))

    def usage(self, service: str) -> tuple[int, int]:
        """Return current UTC-day and named-session usage gauges."""
        with self._lock:
            document = self._load()
            if document["utc_date"] != self._clock.utc_now().date().isoformat():
                return 0, 0
            daily = document["daily"].get(service, 0)
            session = document["sessions"].get(self._session_id, {}).get(service, 0)
            return daily, session

    def _load(self) -> _QuotaDocument:
        data = self._repository.load("gatekeeper-quota")
        if data is None:
            return {"utc_date": "", "daily": {}, "sessions": {}}
        try:
            value = json.loads(data)
            utc_date = value["utc_date"]
            daily = value["daily"]
            sessions = value["sessions"]
            if (
                not isinstance(utc_date, str)
                or not isinstance(daily, dict)
                or not isinstance(sessions, dict)
                or any(type(item) is not int for item in daily.values())
                or any(
                    not isinstance(item, dict)
                    or any(type(count) is not int for count in item.values())
                    for item in sessions.values()
                )
            ):
                raise TypeError
            return _QuotaDocument(utc_date=utc_date, daily=daily, sessions=sessions)
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("durable quota record is invalid") from exc
