"""Audit locked installed dependency licenses for release compatibility."""

import importlib.metadata
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "results/benchmarks/m11_licenses.json"
_FORBIDDEN = re.compile(r"\b(?:AGPL|GPL|PROPRIETARY|COMMERCIAL)\b", re.IGNORECASE)
_REVIEWED_LICENSES = {
    "caio": (
        "Apache-2.0",
        "https://github.com/mosquito/caio/blob/0.9.25/COPYING",
    ),
    "jeepney": ("MIT", "https://pypi.org/pypi/jeepney/0.9.0/json"),
    "secretstorage": ("BSD-3-Clause", "https://pypi.org/pypi/SecretStorage/3.5.0/json"),
}


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).casefold()


def _license(metadata: importlib.metadata.PackageMetadata) -> str:
    expression = metadata.get("License-Expression")
    if expression:
        return expression.strip()
    classifiers = [
        item.removeprefix("License :: OSI Approved :: ")
        for item in metadata.get_all("Classifier", [])
        if item.startswith("License :: OSI Approved :: ")
    ]
    if classifiers:
        return " OR ".join(sorted(classifiers))
    legacy = (metadata.get("License") or "").strip().splitlines()
    return legacy[0][:160] if legacy else "UNKNOWN"


def build_audit(root: Path = ROOT) -> dict[str, object]:
    """Return licenses for every package in the cross-platform lock."""
    packages = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))["package"]
    locked = {
        _normalize(item["name"]): (str(item["name"]), str(item["version"])) for item in packages
    }
    installed = {
        _normalize(name): distribution
        for distribution in importlib.metadata.distributions()
        if (name := distribution.metadata.get("Name"))
    }
    records = []
    for normalized, (locked_name, locked_version) in sorted(locked.items()):
        distribution = installed.get(normalized)
        name = distribution.metadata.get("Name", locked_name) if distribution else locked_name
        license_name = _license(distribution.metadata) if distribution else "UNKNOWN"
        source = "installed package metadata"
        if license_name == "UNKNOWN" and normalized in _REVIEWED_LICENSES:
            license_name, source = _REVIEWED_LICENSES[normalized]
        records.append(
            {
                "name": name,
                "version": distribution.version if distribution else locked_version,
                "license": license_name,
                "license_source": source,
            }
        )
    review = [
        str(item["name"])
        for item in records
        if item["license"] == "UNKNOWN" or _FORBIDDEN.search(str(item["license"]))
    ]
    return {
        "schema_version": "1.0.0",
        "measured_at": "2026-07-26",
        "package_version": "0.10.0",
        "locked_packages": len(locked),
        "audited_locked_packages": len(records),
        "platform_absent_reviewed": sorted(set(locked) - set(installed)),
        "review_required": review,
        "policy": "MIT/BSD/Apache/ISC/PSF/MPL and compatible permissive licenses accepted",
        "dependencies": records,
        "result": "PASS" if len(records) == len(locked) and not review else "FAIL",
    }


def main() -> int:
    """Write the license inventory and fail on absent or incompatible metadata."""
    document = build_audit()
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "locked": document["locked_packages"],
                "audited": document["audited_locked_packages"],
                "review_required": document["review_required"],
                "result": document["result"],
            },
            sort_keys=True,
        )
    )
    return 0 if document["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
