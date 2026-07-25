# Experiment and Competitive Evaluation Policy

**Baseline:** `1.0.0`
**Purpose:** improve league performance without sacrificing protocol correctness, reproducibility, or academic integrity.

## 1. Baselines

| ID | Baseline | Purpose | Required behavior |
|---|---|---|---|
| BL-REF | Clean reimplementation of documented reference-greedy policy | Course/example comparison | Argmax belief plus simple Manhattan pursuit/evasion and documented random barrier behavior; no runtime import |
| BL-RND | Seeded uniformly random legal policy for both roles | Lower-bound sanity check | Samples only engine-provided legal actions |
| BL-SCR-P | Scripted shortest-path Police | Deterministic pursuit benchmark | Shortest legal path with deterministic ties |
| BL-SCR-T | Scripted maximum-distance Thief | Deterministic evasion benchmark | Maximizes safe distance/space with deterministic ties |
| BL-ADV | Curated adversary suite | Robustness | corner/boundary, cycle, switch, aggressive/random barrier, graph-cut, hint-trust profiles |
| BL-PREV | Previous frozen candidate | Regression | Immutable version, commit, config, and metrics |

Primary comparison uses official fixed scoring and paired role-swapped fixtures. Secondary metrics include capture/survival, technical/tamper rate, latency, tokens, calibration, and confidence intervals. Technical or tamper outcomes score exactly as mandated and are reported separately; they are never averaged away.

## 2. Dataset/fixture separation

| Split | Allowed use | Prohibited use | Freeze rule |
|---|---|---|---|
| Training | search, tuning, feature work, failure discovery | claiming final generalization | seeds/configs/adversaries versioned before each campaign |
| Validation | model selection, early stopping, ablation decisions | direct optimization on individual outcomes or migration into training without new split version | disjoint seeds and adversary instances; changes require a new version |
| Holdout | one final unbiased estimate after candidate freeze | prompt/hyperparameter/code adjustment, inspecting hidden fixtures/results early | sealed seed/adversary manifest; opened once under QA procedure |

Leakage policy:

- Seed ranges, board/config families, start schedules, opponent instances, hint profiles, and randomized faults are disjoint.
- Adversary families may span splits only with independently generated instances and declared family-level generalization analysis.
- Post-audit opponent truth from league/replay may not enter live policy training during the same evaluation campaign.
- A discovered holdout defect may be fixed only by invalidating the candidate and creating a fresh holdout version before another claim.
- Raw holdout results are immutable and all attempts, including failures, are reported.

## 3. Reproducibility metadata

Every run writes a manifest containing:

```yaml
experiment_id: globally-unique
parent_campaign_id: versioned-campaign
started_at_utc: RFC3339
code_commit: full-git-sha
dirty_tree: false
package_version: semantic-version
protocol_version: semantic-version
schema_versions: {}
role_export_versions: {}
config_path: relative-path
config_sha256: hex
private_profile_digest: redacted-digest
strategy_id: name-and-version
baseline_or_candidate: classification
split: train|validation|holdout|rehearsal
split_manifest_sha256: hex
seed: integer
opponent_id: name-and-version
role_schedule: []
board_fixture_ids: []
fault_profile_id: name-and-version
hardware:
  os: value
  cpu: value
  cores: integer
  ram_bytes: integer
  gpu: optional
runtime:
  python: value
  uv_lock_sha256: hex
  fastmcp: value
  wall_seconds: number
resources:
  peak_rss_bytes: integer
  request_bytes: integer
  response_bytes: integer
  llm_calls: integer
  prompt_tokens: integer
  completion_tokens: integer
  estimated_cost: decimal-string-and-currency
metrics: {}
artifact_digests: {}
exit_status: typed-status
```

Machine/environment values unavailable on a platform are explicit `null` with a reason; they are never silently omitted.

## 4. Analysis rules

- Use at least paired role-swapped outcomes for fair comparison.
- Report sample size, mean/median as appropriate, variance, bootstrap confidence intervals, and family-level results.
- Predeclare the primary metric and candidate-selection rule.
- Persist every attempted configuration and stopped trial.
- Include ablations for belief fusion, search, opponent model, graph barriers, risk, and deception.
- Measure wall time, CPU, memory, requests, bytes, tokens, and monetary cost.
- Reject any candidate that improves score by causing illegal actions, deadline breaches, integrity failures, or technical losses.
- Holdout passes only when the frozen candidate meets correctness/reliability gates and the competitive thresholds in `docs/EVIDENCE.md`.

## 5. Evidence locations

- machine-readable raw outputs: `results/`;
- plots and rendered tables: `assets/`;
- exploratory but reproducible analysis: `notebooks/`;
- hypotheses/method/results/limitations: `docs/RESEARCH_REPORT.md`;
- immutable candidate and split manifests: `results/manifests/`.

These directories are created in their implementation milestones. M0 defines the contract only.

