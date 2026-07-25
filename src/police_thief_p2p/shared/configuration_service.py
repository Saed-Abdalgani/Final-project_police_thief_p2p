"""Higher-level configuration composition and comparison operations."""

from pathlib import Path

from police_thief_p2p.shared.canonical_json import DocumentComparison, digest_bytes
from police_thief_p2p.shared.config_loader import (
    load_private_path,
    load_shared_bytes,
    load_shared_path,
)
from police_thief_p2p.shared.effective_config import EffectiveConfig, merge_effective_config


def load_effective_paths(shared_path: Path, private_path: Path) -> EffectiveConfig:
    """Load both files and preserve shared/private provenance."""
    return merge_effective_config(load_shared_path(shared_path), load_private_path(private_path))


def compare_shared_documents(left: bytes, right: bytes) -> DocumentComparison:
    """Compare exact bytes and canonical semantic digests independently."""
    left_config = load_shared_bytes(left, source="left:game.json")
    right_config = load_shared_bytes(right, source="right:game.json")
    return DocumentComparison(
        byte_identical=left == right,
        semantic_digest_equal=left_config.digest() == right_config.digest(),
        left_raw_digest=digest_bytes(left),
        right_raw_digest=digest_bytes(right),
        left_semantic_digest=left_config.digest(),
        right_semantic_digest=right_config.digest(),
    )
