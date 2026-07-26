# M11 Platform Record

**Candidate:** `0.10.0`
**Recorded:** 2026-07-26

The supported CI matrix is Windows Latest on CPython 3.13 and 3.14 for frozen
sync, repository validators, Ruff, strict mypy, the full coverage suite, and
distribution builds. macOS Latest on CPython 3.13 performs frozen sync, package
import, SDK readiness, and the version smoke test. The complete matrix passed in
[quality run 30201853430](https://github.com/Saed-Abdalgani/Final-project_police_thief_p2p/actions/runs/30201853430)
for implementation commit `c07e26174ba0dd046f244fb4c56937750507893e`.

Local measurement used Windows 11 `10.0.26200`, CPython 3.13.13, four CPU cores,
and 8 GB RAM. All local static, functional, security, chaos, mutation, soak, and
performance gates passed.

The only platform-specific limitation is unprivileged symlink/reparse-point
creation. On Windows hosts without Developer Mode or the required privilege, the
symlink escape test reports an explicit capability skip. Path normalization,
resolved-root containment, malicious identifier, manifest-link, filename, and
archive traversal tests still execute. On filesystems that permit symlink
creation, the same test must execute and reject the escape.

No gameplay, scoring, canonical byte, commitment, replay, or artifact behavior is
platform-specific. Monotonic clocks own deadlines; canonical JSON owns wire and
digest bytes; filesystem writes resolve beneath configured roots.
