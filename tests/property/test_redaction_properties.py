import pytest
from hypothesis import given
from hypothesis import strategies as st

from police_thief_p2p.constants import REDACTED
from police_thief_p2p.shared.redaction import redact_value

pytestmark = [pytest.mark.property, pytest.mark.security]


@given(st.text(min_size=1))
def test_sensitive_mapping_values_never_survive_redaction(secret: str) -> None:
    redacted = redact_value({"access_token": secret})
    assert redacted == {"access_token": REDACTED}


@given(st.binary(min_size=1))
def test_bytes_are_never_logged_as_plain_values(secret: bytes) -> None:
    assert redact_value(secret) == REDACTED
