# Desktop + Laptop Playtest Runbook

Use **one git commit on both machines**. You do not need a second person's
project — only this repository cloned twice (desktop + laptop).

## What this proves

| Layer | Command / action | Needs 2 machines? |
|---|---|---|
| Install + readiness | `uv sync` + `police-thief-p2p readiness` | No |
| Dual-process MCP | pytest dual-process | No |
| Loopback league dress rehearsal | `scripts.run_m12_league_rehearsal` | No |
| Screenshots / replay assets | `scripts/generate_m10_screenshots.py` | No |
| Public-tunnel counted series | peers + `cloudflared` + remote driver | **Yes** |
| Live GUI | `python -m police_thief_p2p.adapters.gui` | Optional |

## Phase A — same machine (run on desktop first)

```powershell
cd "c:\Users\lovel\Desktop\ai orcherstration final project"
git pull
uv run python -m scripts.run_local_playtest_suite
```

Expect final JSON `"result": "PASS"`.

## Phase B — two machines over Cloudflare quick tunnels (no TOML editing)

You do **not** edit `opponent_public_url` by hand. Auto-write local configs, start
each peer + tunnel, then paste the two printed `https://….trycloudflare.com`
origins into the driver command (append `/mcp`).

### Prerequisites (both machines)

```powershell
git pull
git rev-parse HEAD
uv sync --frozen --all-groups
winget install --id Cloudflare.cloudflared -e
uv run python -m scripts.write_playtest_configs
```

`git rev-parse HEAD` must match on desktop and laptop.

### Desktop = Police (two terminals; leave both open)

Terminal 1:

```powershell
uv run python -m scripts.write_playtest_configs
uv run python -m police_thief_p2p.adapters.mcp.peer_process --shared-config config/shared/game.example.json --private-config config/private/police.playtest.toml
```

Terminal 2:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Copy the printed `https://….trycloudflare.com` value. That is `DESKTOP_URL`.

### Laptop = Thief (two terminals; leave both open)

Terminal 1:

```powershell
uv run python -m scripts.write_playtest_configs
uv run python -m police_thief_p2p.adapters.mcp.peer_process --shared-config config/shared/game.example.json --private-config config/private/thief.playtest.toml
```

Terminal 2:

```powershell
cloudflared tunnel --url http://127.0.0.1:8000
```

Copy the printed `https://….trycloudflare.com` value. That is `LAPTOP_URL`.

### Drive the counted series (either machine; one paste)

Replace the two placeholders with the exact tunnel origins (keep `/mcp`):

```powershell
uv run python -m scripts.run_remote_league_playtest --police-url "https://DESKTOP_URL.trycloudflare.com/mcp" --thief-url "https://LAPTOP_URL.trycloudflare.com/mcp"
```

Evidence: `results/benchmarks/two_machine_playtest.json`.
`external_network_tunnels_verified` is true only when both URLs are public HTTPS.

## Phase C — watch a finished game (replay)

The tunnel playtest proves the protocol; **replay** is how you visually step through a finished match.

```powershell
uv run python -m scripts.run_replay_demo
```

In the window: **Play** auto-advances frames; **Next** / **Previous** step manually; banner should say **Verified OK**.

Headless check only:

```powershell
uv run python -m scripts.run_replay_demo --no-gui
uv run police-thief-p2p replay verify --manifest results/replay-demo/manifest.json --artifact-root results/replay-demo --group GRP00001 --sub-game 1
```

## Phase D — optional local GUI (local-truth monitor, not the match movie)

```powershell
uv run python -m police_thief_p2p.adapters.gui
```

## Phase E — report dry-run (when you have a manifest)

```powershell
uv run police-thief-p2p report validate `
  --manifest <artifact-root>/official/manifest_<game-id>.json `
  --artifact-root <artifact-root> `
  --sender your-account@gmail.com
```

## Same Wi‑Fi LAN alternative (not competition-grade)

If both machines share a LAN and you only want a connectivity smoke test, you can
point `opponent_public_url` at `http://<other-lan-ip>:8000/mcp` with
`listen_host = "0.0.0.0"`. Counted **competition** claims still require public
HTTPS tunnels (Phase B).

## Stop conditions

- Preflight prints `police_ok`/`thief_ok` false → tunnel URL wrong or peer down.
- Remote gates `FAIL` → capture both peer logs and the evidence JSON.
- Do not start counted play until bidirectional health succeeds.
