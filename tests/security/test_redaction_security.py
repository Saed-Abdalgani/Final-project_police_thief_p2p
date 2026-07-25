import pytest

from police_thief_p2p.constants import REDACTED
from police_thief_p2p.shared.redaction import redact_value

pytestmark = pytest.mark.security


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "api_key",
        "Authorization",
        "commit_nonce",
        "oauth-token",
        "private_key",
        "credentials",
    ],
)
def test_security_sensitive_key_families_are_redacted(key: str) -> None:
    assert redact_value({key: "do-not-log"}) == {key: REDACTED}
