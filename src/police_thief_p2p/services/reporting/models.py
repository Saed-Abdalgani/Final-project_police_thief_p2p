"""Durable report outbox state and transition contract."""

from enum import StrEnum
from typing import Annotated

from pydantic import Field, StrictInt, StrictStr

from police_thief_p2p.services.artifacts.common import Digest
from police_thief_p2p.shared.config_sections import DecimalText, FrozenModel


class OutboxState(StrEnum):
    """Persisted report delivery lifecycle."""

    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    SENDING = "SENDING"
    RETRY_WAIT = "RETRY_WAIT"
    SENT = "SENT"
    FAILED_PERMANENT = "FAILED_PERMANENT"


_TRANSITIONS = {
    OutboxState.PENDING: {OutboxState.VALIDATED},
    OutboxState.VALIDATED: {OutboxState.SENDING},
    OutboxState.SENDING: {
        OutboxState.RETRY_WAIT,
        OutboxState.SENT,
        OutboxState.FAILED_PERMANENT,
    },
    OutboxState.RETRY_WAIT: {OutboxState.VALIDATED},
    OutboxState.SENT: set(),
    OutboxState.FAILED_PERMANENT: set(),
}


class OutboxItem(FrozenModel):
    """One immutable snapshot of a logical report delivery."""

    logical_report_id: Digest
    game_uid: StrictStr
    sender_group_id: StrictStr
    attachment_name: StrictStr
    attachment_sha256: Digest
    attachment_b64: StrictStr
    recipient: StrictStr
    state: OutboxState = OutboxState.PENDING
    attempts: Annotated[StrictInt, Field(ge=0)] = 0
    provider_id: StrictStr | None = None
    last_error_code: StrictStr | None = None
    retry_not_before: DecimalText | None = None

    def transitioned(self, state: OutboxState, **changes: object) -> "OutboxItem":
        """Return a validated next state or reject illegal mutation."""
        if state not in _TRANSITIONS[self.state]:
            raise ValueError(f"illegal outbox transition {self.state} -> {state}")
        allowed = {"provider_id", "last_error_code", "retry_not_before"}
        if set(changes) - allowed:
            raise ValueError("outbox transition attempted immutable-field mutation")
        update = {"state": state, **changes}
        if state is OutboxState.SENDING:
            update["attempts"] = self.attempts + 1
        document = self.model_dump(mode="json")
        document.update(update)
        return OutboxItem.model_validate(document)
