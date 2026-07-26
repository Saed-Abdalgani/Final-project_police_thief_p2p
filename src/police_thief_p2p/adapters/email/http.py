"""Small injectable HTTP boundary for Gmail and OAuth."""

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HttpResponse:
    """Bounded HTTP response needed by email adapters."""

    status: int
    headers: Mapping[str, str]
    body: bytes


def post(
    url: str,
    body: bytes,
    headers: Mapping[str, str],
    timeout_sec: float,
) -> HttpResponse:
    """POST bounded bytes and preserve HTTP error bodies for safe classification."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("email provider URL must be credential-free HTTPS")
    request = urllib.request.Request(  # noqa: S310 - URL is restricted above.
        url, data=body, headers=dict(headers), method="POST"
    )
    try:
        with urllib.request.urlopen(  # noqa: S310 - URL is restricted above.
            request, timeout=timeout_sec
        ) as response:
            data = response.read(1_048_577)
            if len(data) > 1_048_576:
                raise ValueError("email provider response exceeds size limit")
            return HttpResponse(response.status, dict(response.headers.items()), data)
    except urllib.error.HTTPError as exc:
        data = exc.read(1_048_577)
        return HttpResponse(exc.code, dict(exc.headers.items()), data)


def parse_object(data: bytes) -> dict[str, object]:
    """Parse one bounded provider JSON object."""
    if len(data) > 1_048_576:
        raise ValueError("email provider response exceeds size limit")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("email provider response must be a JSON object")
    return value
