# GRP00001 Opponent Interoperability Guide (Public)

**Audience:** remote league opponents  
**Our group ID:** `GRP00001`  
**Our role exports:** Police + Thief standalone repositories below  
**Package / protocol / schema:** `0.11.0` / `0.7.0` / `0.2.0`  
**Canonical freeze (dev monorepo):** `4021b9e98c8d64055117e732489e4b359345f8ee`  
**Police runtime HEAD:** `915b91ddade4026eb05f752549546d5652c109eb`  
**Thief runtime HEAD:** `0349356e866f9ab796ba49ab223710ab4740f23d`  
**Submission tag (both role repos):** `v1.0-submission`

This document is what we send back when another team shares an interop guide.
It describes **our** peer contract. Read Section 0 before scheduling a counted match.

---

## 0. Critical compatibility notice

We received a public guide that describes a **different wire protocol** from ours
(tools named `negotiate` / `receive_turn` / `submit_audit` / `receive_control`,
flat 14-key signed terms, `python -m thief_agent.interop …`).

**Our implementation does not speak that tool inventory.**

| Topic | Their guide (example) | Our implementation |
|---|---|---|
| MCP tools | `negotiate`, `receive_turn`, `submit_audit`, `receive_control` | `health_v1`, `capabilities_v1`, `propose_match_v1`, `accept_match_v1`, `commit_step_v1`, `acknowledge_step_v1`, `reveal_step_v1`, `capture_claim_v1`, `capture_response_v1`, `final_reveal_v1`, `audit_result_v1`, `agree_result_v1`, `peer_status_v1` |
| Shared rules shape | flat 14 signed keys | nested byte-identical `game.json` (schema `0.2.0`) |
| Turn crypto | commit inside one turn message | three-phase commit → ack → reveal |
| Capture on wire | `capture_claim` field every Cop turn | dedicated `capture_claim_v1` / `capture_response_v1` tools |
| Entry CLI | `thief_agent.interop friendly …` | `police_thief_p2p.adapters.mcp.peer_process` + remote driver |

**Physics knobs can look similar** (7×7, 35 moves, 14 barriers, scent 5 / 0.1 / 0.9,
starts `[3,3]` / `[0,0]`, six sub-games) **and still be unplayable** if the MCP
tool names and envelopes differ.

### Decision gate before any official series

Do **not** start a counted match until both teams explicitly confirm one of:

1. **Same wire family:** opponent runs (or adapts to) our FastMCP tool inventory
   and nested `game.json` constitution in this document / `docs/PROTOCOL.md`, **or**
2. **Adapter bridge:** a mutually agreed translator between the two protocols
   (not shipped in our default tree), **or**
3. **Abort / reschedule** with the lecturer if no common wire exists.

A successful `curl` of `/mcp` only proves HTTP reachability. It does **not** prove
tool-name compatibility.

---

## 1. Who we are / which repos apply

| Artifact | URL / value | Used for |
|---|---|---|
| Canonical development monorepo | https://github.com/Saed-Abdalgani/Final-project_police_thief_p2p | Integration, docs, export source |
| Police standalone submission repo | https://github.com/JCS1029/GRP00001-police-p2p | Moodle “Cop” link; Police peer checkout |
| Thief standalone submission repo | https://github.com/JCS1029/GRP00001-thief-p2p | Moodle “Thief” link; Thief peer checkout |

**Where this file lives:** canonical `docs/OPPONENT_INTEROP_GUIDE_PUBLIC.md`
(and should be mirrored into both role exports on the next release refresh).

**Which repo to clone to play us:** clone the **role repo for the role you need
on that machine** (Police or Thief), or clone the canonical monorepo and use the
matching private playtest TOML. Opponents should exchange **both** role-repo URLs
plus the exact 40-hex HEAD they will run.

---

## 2. Ready template (send / fill at match time)

```text
READY

Group:                GRP00001
Members:              <fill non-empty list at match time>
Cop repo:             https://github.com/JCS1029/GRP00001-police-p2p
Thief repo:           https://github.com/JCS1029/GRP00001-thief-p2p
Cop runtime SHA:      915b91ddade4026eb05f752549546d5652c109eb
Thief runtime SHA:    0349356e866f9ab796ba49ab223710ab4740f23d
Public MCP endpoint:  https://<live-trycloudflare-or-host>/mcp
Starting role:        police   (if opponent group starts as thief; else agree)
Agreed game_uid / shared config:  byte-identical game.json (Appendix A)
Protocol family:      FastMCP tool inventory in Section 3 (NOT negotiate/receive_turn)

Shared nested game.json physics match Appendix A:                 YES
Survival threshold = 35 completed steps:                          YES
Capture via capture_claim_v1 / capture_response_v1:               YES
Transport /mcp, no required bearer auth:                          YES
Commit → acknowledge → reveal sealing:                            YES
Final reveal + mutual audit + agree_result:                       YES
Server stays up through audit/agree; graceful stop:               YES
Public endpoint curl-checked immediately before match:            YES (at match time)
Same wire protocol family confirmed with opponent:                REQUIRED
```

Dynamic values (live tunnel URL, member names, exact HEADs if we re-export)
are confirmed in chat immediately before kickoff.

---

## 3. Our MCP tool inventory (must match)

Endpoint path: **`/mcp`**. No bearer token required.

| Tool | Role |
|---|---|
| `health_v1` / `capabilities_v1` | preflight |
| `propose_match_v1` / `accept_match_v1` | negotiate shared constitution |
| `commit_step_v1` → `acknowledge_step_v1` → `reveal_step_v1` | sealed step loop |
| `capture_claim_v1` / `capture_response_v1` | Police claim / Thief truthful answer |
| `final_reveal_v1` / `audit_result_v1` / `agree_result_v1` | nonces + mutual audit + result |
| `peer_status_v1` | safe status |

Session-bound calls use our `protocol_envelope.schema.json` (protocol version
`0.6.0` payloads under package/protocol docs `0.7.0`). Normative detail:
[`PROTOCOL.md`](PROTOCOL.md), [`CRYPTO_AUDIT.md`](CRYPTO_AUDIT.md),
[`CONFIGURATION.md`](CONFIGURATION.md).

---

## 4. Shared constitution (nested `game.json`)

We do **not** negotiate a flat 14-key object. We freeze a **byte-identical**
shared JSON file (example: `config/shared/game.example.json`). Negotiation
binds digests of that constitution.

Physics that align with common course defaults are listed in **Appendix A**.
Extra nested sections (scoring, league timeouts, gatekeeper ceilings, exact
kernel matrix, decimal rounding) are part of **our** signed constitution and
must be agreed if you play our peer.

---

## 5. How to run against us (our stack)

### Our peer boot (example Police on desktop)

```powershell
git clone https://github.com/JCS1029/GRP00001-police-p2p.git
cd GRP00001-police-p2p
git checkout v1.0-submission   # or the agreed 40-hex SHA
uv sync --frozen --all-groups
uv run police-thief-p2p readiness
uv run python -m police_thief_p2p.adapters.mcp.peer_process `
  --shared-config config/shared/game.example.json `
  --private-config config/private/police.playtest.toml
```

Second terminal:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Share the printed `https://….trycloudflare.com` origin; MCP path is `/mcp`.

### Opponent mirror

They boot their Thief (or Police) peer the same way from their repo **only if**
their tool inventory matches Section 3. Then either side drives the series with
our remote playtest driver (canonical / export scripts):

```powershell
uv run python -m scripts.run_remote_league_playtest `
  --police-url "https://<police-host>/mcp" `
  --thief-url "https://<thief-host>/mcp"
```

Short non-counted dual-process proof on one machine:

```powershell
uv run pytest tests/integration/test_dual_process_mcp.py -q
```

---

## 6. Capture / scoring / series (our semantics)

- Series length: **6** sub-games, roles alternate.
- Survival / move ceiling: **35**.
- Capture resolution after sealed reveals; Police claims and Thief responses use
  the dedicated capture tools (not a free-form turn field).
- Scoring table matches the course fixed values (capture 20/5, survival 5/10,
  sanctions 0/0, series tie +2/+2 when totals equal).

If an opponent’s guide requires “Cop emits `capture_claim` inside every turn
message with tools `negotiate`/`receive_turn`”, that is **not** our on-the-wire
shape even when the English capture rules sound similar.

---

## 7. What we need from the other team

Before kickoff, send us:

1. Group id + non-empty member list  
2. Cop + Thief public repo URLs  
3. Exact 40-hex runtime SHAs for the code you will run  
4. Live public `https://…/mcp` URL (curl-verified, tunnel kept up)  
5. Explicit confirmation of **wire family** (Section 0)  
6. Starting roles for sub-game 1  
7. Agreement on the shared nested `game.json` bytes / digests  

If you start as **Thief**, we start as **Police** for sub-game 1 (roles then alternate).

---

## 8. Reciprocal-file policy

Yes — each team should publish a short public interop note like this one.
Receiving a guide does **not** mean we silently adopt the sender’s CLI or tool
names. We reply with **this** document and schedule only after Section 0 is green.

---

## Appendix A — Physics defaults we ship in `game.example.json`

These are the course-aligned numbers in our example constitution (nested form):

| Concept | Our nested path | Value |
|---|---|---|
| Board | `board_and_agents.grid_size` | `7` |
| Origin | `board_and_agents.axis_origin_corner` | `"top-left"` |
| Index base | `board_and_agents.axis_start_index` | `0` |
| Thief start | `board_and_agents.thief_start` | `[3, 3]` |
| Cop start | `board_and_agents.cop_start` | `[0, 0]` |
| Hint cap | `world.hint_max_words` | `15` |
| Moves / survival | `movement_and_barriers.max_moves` / `survival_threshold` | `35` / `35` |
| Barriers | `movement_and_barriers.max_barriers` | `14` |
| Scent grid | `pheromones.pheromone_grid_size` | `5` |
| Scent center / decay | `pheromones.pheromone_center_intensity` / `pheromone_decay` | `"0.9"` / `"0.10"` (decimal strings) |
| Sub-games | `network_and_league.num_games` | `6` |

Note: our scent model also ships an explicit **kernel matrix** and rounding mode.
A flat 14-key guide that omits the kernel is **not** byte-equivalent to our file.

---

## Appendix B — Pointers

- Protocol: [`PROTOCOL.md`](PROTOCOL.md)  
- Config: [`CONFIGURATION.md`](CONFIGURATION.md)  
- Playtest runbook: [`PLAYTEST.md`](PLAYTEST.md)  
- Moodle paste pack: [`evidence/MOODLE_FORM_PACKAGE.md`](evidence/MOODLE_FORM_PACKAGE.md)  
- Two-machine tunnel evidence: `results/benchmarks/two_machine_playtest.json`
