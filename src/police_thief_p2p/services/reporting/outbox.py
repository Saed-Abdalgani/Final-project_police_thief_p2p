"""Atomic single-record outbox resilient to every process boundary."""

import json
from threading import RLock

from pydantic import ValidationError

from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.services.reporting.models import OutboxItem, OutboxState
from police_thief_p2p.shared.canonical_json import canonical_json_bytes


class DurableOutbox:
    """Persist all logical reports in one atomic repository record."""

    __slots__ = ("_lock", "_repository")

    def __init__(self, repository: RepositoryPort) -> None:
        """Create a crash-recovering outbox over an atomic byte repository."""
        self._repository = repository
        self._lock = RLock()
        self._recover_interrupted()

    def enqueue(self, item: OutboxItem) -> OutboxItem:
        """Enforce logical-report idempotency and reject conflicting bytes."""
        with self._lock:
            items = self._load()
            existing = items.get(item.logical_report_id)
            if existing is not None:
                if (
                    existing.attachment_sha256 != item.attachment_sha256
                    or existing.recipient != item.recipient
                ):
                    raise ValueError("logical report ID conflicts with durable outbox")
                return existing
            items[item.logical_report_id] = item
            self._save(items)
            return item

    def get(self, logical_report_id: str) -> OutboxItem:
        """Return one durable report or raise a stable lookup failure."""
        with self._lock:
            try:
                return self._load()[logical_report_id]
            except KeyError as exc:
                raise KeyError("logical report is not present in outbox") from exc

    def transition(
        self,
        logical_report_id: str,
        state: OutboxState,
        **changes: object,
    ) -> OutboxItem:
        """Atomically persist one legal state transition."""
        with self._lock:
            items = self._load()
            item = items[logical_report_id].transitioned(state, **changes)
            items[logical_report_id] = item
            self._save(items)
            return item

    def items(self) -> tuple[OutboxItem, ...]:
        """Return stable logical-report order for restart dispatch."""
        with self._lock:
            values = self._load()
            return tuple(values[key] for key in sorted(values))

    def _recover_interrupted(self) -> None:
        with self._lock:
            items = self._load()
            changed = False
            for key, item in tuple(items.items()):
                if item.state is OutboxState.SENDING:
                    items[key] = item.transitioned(
                        OutboxState.RETRY_WAIT,
                        last_error_code="INTERRUPTED_DURING_SEND",
                    )
                    changed = True
            if changed:
                self._save(items)

    def _load(self) -> dict[str, OutboxItem]:
        data = self._repository.load("outbox")
        if data is None:
            return {}
        try:
            raw = json.loads(data)
            items = [OutboxItem.model_validate(item) for item in raw["items"]]
        except (KeyError, TypeError, json.JSONDecodeError, ValidationError) as exc:
            raise ValueError("durable outbox record is invalid") from exc
        if len({item.logical_report_id for item in items}) != len(items):
            raise ValueError("durable outbox contains duplicate logical reports")
        return {item.logical_report_id: item for item in items}

    def _save(self, items: dict[str, OutboxItem]) -> None:
        document = {
            "version": 1,
            "items": [items[key].model_dump(mode="json") for key in sorted(items)],
        }
        self._repository.save("outbox", canonical_json_bytes(document))
