"""Canonical signed Step-0 declaration and opaque signing material."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from collections.abc import Mapping
from typing import BinaryIO

from pydantic import StrictBool, StrictInt, StrictStr, model_validator

from police_thief_p2p.services.ports.git_info import GitState
from police_thief_p2p.services.ports.system_info import SystemInfo
from police_thief_p2p.services.protocol.envelope import ProtocolModel
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.identifiers import GroupId

_COMMIT = re.compile(r"^[a-f0-9]{40}$")
_DIGEST = re.compile(r"^[a-f0-9]{64}$")


class SigningKey:
    """Opaque HMAC key that cannot be printed or serialized."""

    __slots__ = ("__value",)

    def __init__(self, value: bytes) -> None:
        """Copy validated secret bytes into an opaque object."""
        if not isinstance(value, bytes) or len(value) < 32:
            raise ValueError("Step-0 signing material must contain at least 256 bits")
        self.__value = bytes(value)

    def sign(self, payload: bytes) -> str:
        """Return a lowercase HMAC-SHA-256 signature."""
        return hmac.new(self.__value, payload, hashlib.sha256).hexdigest()

    def __repr__(self) -> str:
        """Never disclose signing material."""
        return "SigningKey(<redacted>)"

    __str__ = __repr__


def load_signing_key(
    *,
    env_name: str | None = None,
    environ: Mapping[str, str] | None = None,
    file_handle: BinaryIO | None = None,
) -> SigningKey:
    """Load a key from exactly one secret environment name or open binary handle."""
    if (env_name is None) == (file_handle is None):
        raise ValueError("provide exactly one Step-0 signing-key source")
    if file_handle is not None:
        material = file_handle.read()
    else:
        source = os.environ if environ is None else environ
        material = source.get(env_name or "", "").encode()
    if not material:
        raise ValueError("Step-0 signing material is unavailable")
    return SigningKey(material)


class SystemDeclaration(ProtocolModel):
    """Redacted public hardware and runtime facts with explicit unknowns."""

    operating_system: StrictStr
    platform: StrictStr
    python_version: StrictStr
    cpu_model: StrictStr | None
    cpu_cores: StrictInt | None
    cpu_frequency_mhz: StrictInt | None
    memory_bytes: StrictInt | None
    gpu_model: StrictStr | None
    vram_bytes: StrictInt | None


class GitDeclaration(ProtocolModel):
    """Exact played source revision."""

    commit: StrictStr | None
    dirty: StrictBool | None


class StepZeroBody(ProtocolModel):
    """Every declaration and negotiated artifact bound before play."""

    declaration_version: str = "1.0.0"
    group_id: StrictStr
    counted: StrictBool
    template_mode: StrictBool
    model_provider: StrictStr
    model_name: StrictStr
    estimated_tokens: StrictInt
    system: SystemDeclaration
    git: GitDeclaration
    config_sha256: StrictStr
    scent_model_sha256: StrictStr
    role_schedule_sha256: StrictStr
    protocol_version: StrictStr
    schema_version: StrictStr

    @model_validator(mode="after")
    def validate_binding(self) -> StepZeroBody:
        """Reject uncountable revisions, invalid identities, and unbound digests."""
        GroupId(self.group_id)
        if self.estimated_tokens < 0 or (self.template_mode and self.estimated_tokens != 0):
            raise ValueError("template mode must declare zero operational tokens")
        for value in (
            self.config_sha256,
            self.scent_model_sha256,
            self.role_schedule_sha256,
        ):
            if _DIGEST.fullmatch(value) is None:
                raise ValueError("Step-0 digest field is invalid")
        if self.counted and (
            self.git.commit is None
            or _COMMIT.fullmatch(self.git.commit) is None
            or self.git.dirty is not False
        ):
            raise ValueError("counted Step-0 requires a known clean exact Git commit")
        return self

    def canonical_bytes(self) -> bytes:
        """Return the immutable cross-platform declaration bytes."""
        return canonical_json_bytes(self.model_dump(mode="json"))

    @classmethod
    def compose(
        cls,
        *,
        system: SystemInfo,
        git: GitState,
        **terms: object,
    ) -> StepZeroBody:
        """Compose public port DTOs into the signed declaration model."""
        return cls.model_validate(
            {
                **terms,
                "system": {name: getattr(system, name) for name in SystemDeclaration.model_fields},
                "git": {"commit": git.commit, "dirty": git.dirty},
            }
        )


class SignedStepZero(ProtocolModel):
    """Signed declaration whose secret key is never present."""

    body: StepZeroBody
    signature_sha256: StrictStr

    @classmethod
    def create(cls, body: StepZeroBody, key: SigningKey) -> SignedStepZero:
        """Sign exact canonical Step-0 bytes."""
        return cls(body=body, signature_sha256=key.sign(body.canonical_bytes()))

    def verify(self, key: SigningKey) -> bool:
        """Verify the signature using a constant-time comparison."""
        return secrets.compare_digest(
            key.sign(self.body.canonical_bytes()),
            self.signature_sha256,
        )
