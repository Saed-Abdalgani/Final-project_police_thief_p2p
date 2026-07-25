"""Step-0 declaration contract prepared for later cryptographic sealing."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, StrictBool, StrictInt, StrictStr

from police_thief_p2p.services.protocol.envelope import ProtocolModel


class HardwareDeclaration(ProtocolModel):
    """Required runtime hardware and operating-system declaration."""

    operating_system: StrictStr
    cpu_model: StrictStr
    cpu_cores: Annotated[StrictInt, Field(ge=1)]
    cpu_frequency_mhz: Annotated[StrictInt, Field(ge=1)] | None
    ram_bytes: Annotated[StrictInt, Field(ge=1)]
    gpu_model: StrictStr | None
    vram_bytes: Annotated[StrictInt, Field(ge=0)] | None
    timezone: StrictStr


class SoftwareDeclaration(ProtocolModel):
    """Required code, provider, and bounded-token declaration."""

    code_version: StrictStr
    played_commit: StrictStr
    model_provider: StrictStr
    model_name: StrictStr
    estimated_tokens: Annotated[StrictInt, Field(ge=0)]
    llm_movement_enabled: StrictBool = False


class StepZeroDeclaration(ProtocolModel):
    """Complete public declaration captured before live play."""

    group_id: StrictStr
    hardware: HardwareDeclaration
    software: SoftwareDeclaration
    declaration_digest: StrictStr | None = None
