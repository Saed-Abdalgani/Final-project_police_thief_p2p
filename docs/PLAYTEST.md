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

## Phase D2 — amireman-wire DEMO (4-tool compatibility peer)

Against teams that speak `negotiate` / `receive_turn` / `submit_audit` /
`receive_control` (not our `_v1` tools), run the dedicated adapter. This path is
**DEMO / friendly only** (`match_mode=friendly`, never emails the lecturer).

Local loopback smoke (two terminals):

```powershell
# Terminal A — we start as Police for sub-game 1
uv run python -m police_thief_p2p.adapters.amireman.interop friendly `
  --peer http://127.0.0.1:8902/mcp --role police --group saedshki `
  --host 127.0.0.1 --port 8901 --games 2 --game-id DEMO-LOCAL `
  --public-mcp-url http://127.0.0.1:8901/mcp `
  --member "Your Name" --member "Teammate Name" `
  --terms config/shared/amireman.game.json `
  --out results/amireman-demo/local-a --verbose

# Terminal B — complementary Thief peer (or the real opponent)
uv run python -m police_thief_p2p.adapters.amireman.interop friendly `
  --peer http://127.0.0.1:8901/mcp --role thief --group amireman `
  --host 127.0.0.1 --port 8902 --games 2 --game-id DEMO-LOCAL `
  --public-mcp-url http://127.0.0.1:8902/mcp `
  --member "Amir Fadila" --member "Eman Sarhan" `
  --terms config/shared/amireman.game.json `
  --out results/amireman-demo/local-b --verbose
```

For the real remote DEMO: exchange live `https://…/mcp` URLs, use `--games 6`,
keep `--role police` (they start as Thief), and do **not** run Phase E lecturer
send on DEMO artifacts.

## Phase E — report dry-run / send (when you have a manifest)

Dry-run (no Gmail call):

```powershell
uv run police-thief-p2p report validate `
  --manifest <artifact-root>/official/manifest_<game-id>.json `
  --artifact-root <artifact-root> `
  --sender your-account@gmail.com
```

Send to the allowlisted recipient in `config/private/police.playtest.toml`
(first run opens a browser for Gmail send-only OAuth; creates `secrets/token.json`):

```powershell
uv run python -m scripts.send_series_report `
  --manifest <artifact-root>/official/manifest_<game-id>.json `
  --artifact-root <artifact-root> `
  --send
```

Local OAuth rehearsal without a real opponent series:

```powershell
uv run python -m scripts.send_series_report --demo --send
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
