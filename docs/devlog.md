# KLEX Devlog & Extension Guide

This file is the project's memory. It lets anyone (a future contributor, a maintainer, or
another coding session of an AI agent) pick up exactly where things left off.
Keep it dated and honest. Newest entries on top.

---

## 2026-09-11 · polish: tutorials, recordings, mempool fee-order fix

- Site: fixed dead `#quickstart` anchor; added "In plain words" intro section,
  tutorial page with embedded asciinema player (`site/tutorial.html`),
  sessions recorded live via `tools/record_demo.py` (real pty, real mining).
- README: readable figlet wordmark, "New to crypto?" section, glossary links
  (pipx, ML-DSA/FIPS 204, SHA-3, liboqs, PBKDF2/Fernet), tutorials table.
- Written walkthroughs: `docs/tutorials/01-first-block.md`,
  `02-send-and-receive.md` — steps, expected output, troubleshooting tables.
- **Bug found by recording session 2**: `mine_block` sorted pending txs by
  fee only — a high-fee nonce-2 tx was validated before the pending nonce-1
  tx from the same sender and wrongly dropped as stale. Fixed with per-sender
  queue selection (nonce order respected, fee preference between senders);
  regression tests added (`test_multi_pending_with_fees_all_mined`,
  `test_high_fee_pending_does_not_drop_valid_tx`). 49 tests green.
- Recorder fix: child env must be passed via `execvpe`, not `execvp` —
  otherwise PS1/KLEX_WALLET_PASS silently never reach the demo shell.

## 2026-09-11 · published: repo + site + CI

- Repo live: https://github.com/logicbreaks/klex-coin (public, MIT)
- Site live: https://logicbreaks.github.io/klex-coin/ (deployed by
  `.github/workflows/pages.yml`, deploy-on-push of `site/`)
- CI green on first full run: ubuntu/macos/windows × py3.10/3.12 + docker build
- For the custom .de domain: follow `site/README.md` (add CNAME file + DNS),
  Pages is already in "workflow" build mode.
- Fixed along the way (lessons, keep for future):
  - workflow YAML: a step name with a second `:` must be quoted
  - `test_typo_rejected`: the LAST base32 char of an address may carry
    padding bits only — single-char typos there are not guaranteed rejected;
    the test now mutates every checksum-relevant position instead
  - CLI accepts global options in any position (`_hoist_global_args` in
    `klex/cli.py`) — users naturally write `klex mine --datadir X`

## 2026-09-11 · v1.0.0 — built overnight, end to end

### What was built
- Complete PoW chain (`klex/chain.py`): account model, ML-DSA (FIPS 204)
  signatures, KlexHash (double SHA3-256), 60 s target, retarget every 10 blocks
  with ±2 step clamp, 21M cap with halvings, whole-KLEX integers.
- Deterministic genesis block carrying the founding message; hash is hard-coded
  in `klex/crypto.py` as `EXPECTED_GENESIS_HASH` — the chain's identity.
- Wallet (`klex/wallet.py`): ML-DSA-44 keypairs, `KLEX1…` addresses (SHA3-based
  checksum), Fernet+PBKDF2(600k) keystore, `KLEX_WALLET_PASS` env for
  automation, `klex wallet rekey` for handover.
- Node (`klex/node.py`): atomic JSON persistence, mempool with **projected
  state** (several pending txs per sender are allowed, stale txs are dropped at
  mining time), full `verify()` recompute.
- Miner (`klex/miner.py`): canonical-bytes hot loop, re-verified via canonical
  path. Difficulty 5 ≈ 3–5 s/block on a decent CPU.
- P2P (`klex/net.py`): newline-JSON over TCP; `klex serve` / `klex sync`.
  Peers re-validate every block on arrival; invalid blocks are rejected.
- Explorer (`klex/explorer.py`): Flask, binds 127.0.0.1 only.
- Certificate (`klex/paper.py`): printable A4 HTML + embedded SVG QR.
- Docker (`Dockerfile`, `docker-compose.yml`): non-root slim image, volume for
  `/data`, node + explorer + seed services.
- Packaging (`pyproject.toml`): pip/pipx-installable `klex` command.
- CI (`.github/workflows/ci.yml`): test matrix ubuntu/macos/windows ×
  py3.10/3.12 + docker build job.
- Tests: 49 — tampering, forgery, double-spend, invalid PoW, corruption,
  malicious peer, keystore, retarget math.

### Design decisions and why
- **Account model, not UTXO**: far fewer ways to make a correctness mistake in
  one night; balances are trivially auditable.
- **dilithium-py (pure Python reference)**: correct (passes NIST KATs), zero C
  build pain, works everywhere — at the cost of speed and side-channel
  hardening. Documented; liboqs is the v1.2 upgrade.
- **Genesis identity hard-coded**: message is consensus-critical; nothing about
  the founding story can be edited retroactively.
- **Mempool projection**: `submit_transfer` validates against chain state plus
  pending txs, so one sender can queue multiple transfers; `mine_block`
  silently drops stale txs instead of failing.
- **Difficulty clamps (±2, range 3–8)**: a tiny network must never get stuck at
  an unreachable difficulty. Honest trade-off: can't exceed ~16^8.
- **No real names anywhere**: alias "Klex" only; message is pseudonymous.

### Known limitations (v1)
- `net.serve` serves the in-memory block list; blocks mined after a server
  starts are not visible to peers until it restarts.
- `verify()` is O(n²) in practice (`blocks[:i]` slices) — fine below a few
  thousand blocks; switch to incremental anchors in v1.2.
- Single-file JSON storage; SQLite would be the first storage upgrade.
- Python miner ~200–250 kH/s single core; parallelism and a memory-hard
  element are roadmap items.
- Explorer and P2P bind localhost by default — good for safety, needs
  explicit intent to become public.

### Extension guide — where to add what
| Want to change | Touch |
|---|---|
| Chain constants (supply, timing) | `klex/config.py` — consensus-critical, coordinated change |
| New transaction type | `klex/tx.py` (`TYPES`, `build_*`, `structural_check`, `validate`, `apply`) + block rules in `chain.py` |
| PoW function | `klex/crypto.py` `khash()` + `klex/miner.py` hot loop — must stay canonical-compatible |
| P2P protocol messages | `klex/net.py` (`GET_CHAIN`/`CHAIN` are the v1 verbs) |
| Explorer pages | `klex/explorer.py` (routes + `render_*`) |
| Keystore format | `klex/wallet.py` (`KEYSTORE_VERSION` bump) |
| Storage | `klex/node.py` (`read_json`/`atomic_write_json` are the seam) |

Rule of thumb: consensus-critical files (`config.py`, `chain.py`, `tx.py`,
`crypto.py`, `genesis.py`) change only with a version bump and a written
migration note here.

### Security review checklist (for hand-testing the warm-up)
Try these against a running node; every one should fail cleanly:
1. Edit any byte inside `chain.json` → `klex verify` reports the exact block.
2. Re-sign someone else's tx with your key → `submit_transfer` rejects.
3. Send more than your balance → rejected before mempool.
4. Replay the same signed tx → duplicate rejected.
5. Corrupt `chain.json` (truncate the file) → node refuses to load with a
   clear message.
6. Point `klex sync` at a malicious peer that sends fake blocks → rejected,
   local height unchanged (see `tests/test_attack.py`).
7. Try a tx with a negative / huge / float amount → rejected at construction.
8. Genesis message edit → hash mismatch → every node refuses.
9. Wrong keystore passphrase → decrypt fails, secret never touches disk.
10. `klex explore` — confirm it listens on 127.0.0.1 only (never expose it
    without a reverse proxy + TLS).

### Resume checklist for the next session
1. Read this file top-down.
2. `python -m unittest discover -s tests -t .` must pass before touching code.
3. Check the roadmap below; work top-down, keep commits atomic.

### Roadmap
- [ ] v1.1: seed node on a free-tier VPS; public explorer behind a reverse
      proxy; `serve` re-reads chain.json per request (fix staleness)
- [ ] v1.1: Docker smoke on a real daemon; compose hardened (rootless)
- [ ] v1.2: ML-DSA via liboqs (side-channel hardened); KlexHash memory
      element; multi-core miner
- [ ] v1.2: SQLite state backend; `verify` streaming
- [ ] v2: Rust core (single static binary, same consensus rules)
- [ ] research: stealth addresses (privacy), respecting the Monero bar
- [ ] optional: 1:1 wrapped KLEX on an L2, small honest pool, never marketed
      as an investment