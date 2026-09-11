# KLEX

[![ci](https://github.com/logicbreaks/klex-coin/actions/workflows/ci.yml/badge.svg)](https://github.com/logicbreaks/klex-coin/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A post-quantum, fair-launch proof-of-work coin, built from scratch as an open
experiment. Runs on Linux, macOS, and Windows (CI proves it on all three), or
in Docker.

```
 ____  __.__                 
|    |/ _|  |   ____ ___  ___
|      < |  | _/ __ \\  \/  /
|    |  \|  |_\  ___/ >    < 
|____|__ \____/\___  >__/\_ \
        \/         \/      \/
```

**KLEX** is its own blockchain: every transaction is signed with the NIST
post-quantum signature standard **ML-DSA** (FIPS 204), every block is mined
with real CPU work, and the genesis block carries one message that can never be
changed.

Genesis block hash (hard-coded chain identity):
`e62c84b217ee71ac7a3da19b36545956aa4e16aad1911e7f72f50529925868ee`

> "Built overnight with zero budget and full intent, for the one who taught me
> the future is built, not bought. Fair launch. No premine. Value starts at
> zero — like everything great. — K"

---

## New to crypto? Read this first

Five sentences, then you know what this is:

- A **[blockchain](https://en.wikipedia.org/wiki/Blockchain)** is an append-only
  ledger that many computers agree on. Entries can be added; history cannot be
  secretly rewritten — each block locks in the previous one with a hash.
- **KLEX is its own blockchain**, not a token on someone else's chain. Its
  rules, its ledger, its software — all in this repo, ~1,400 lines of Python.
- **[Proof of work](https://en.wikipedia.org/wiki/Proof_of_work)** means a new
  block is only accepted if your computer burned real CPU work solving a puzzle.
  That is "mining", and it pays 50 KLEX per block.
- A **wallet** is a keypair on your disk, protected by a passphrase. The private
  key signs transactions; whoever holds it controls the coins. No account, no
  company, no reset button.
- **Post-quantum** means the signatures use
  **[ML-DSA (NIST FIPS 204)](https://csrc.nist.gov/pubs/fips/204/final)** —
  lattice-based math designed to survive quantum computers, unlike the
  elliptic-curve signatures older coins use.

More depth: [whitepaper](docs/whitepaper.md) ·
[project devlog & extension guide](docs/devlog.md)

## Tutorials — start here

Recorded, real sessions (mining takes the time mining takes) plus written
step-by-step walkthroughs with expected output and troubleshooting:

| | What you do | Read | Watch |
|---|---|---|---|
| 1 | Zero → running node → first mined block → verify | [tutorial-01](docs/tutorials/01-first-block.md) | [recorded session](https://logicbreaks.github.io/klex-coin/tutorial.html) |
| 2 | Second wallet → signed transfer → fee priority → verify | [tutorial-02](docs/tutorials/02-send-and-receive.md) | [recorded session](https://logicbreaks.github.io/klex-coin/tutorial.html) |

Sessions were recorded with [asciinema](https://asciinema.org) from a real
terminal; the recorder ships in the repo (`tools/record_demo.py`) so you can
reproduce or re-record them.

## What this is

A small but **real** cryptocurrency, complete in one repo:

- **Own blockchain** — blocks, transactions, difficulty retargeting, full
  re-verification (`klex verify` re-validates everything from genesis)
- **Post-quantum signatures** — ML-DSA on every transaction
- **Proof of work** — KlexHash = double
  [SHA-3](https://en.wikipedia.org/wiki/SHA-3), CPU-mined, 60 s block target
- **Wallet** — ML-DSA keypairs, `KLEX1…` addresses with checksums,
  passphrase-encrypted keystore
  ([PBKDF2](https://en.wikipedia.org/wiki/PBKDF2) +
  [Fernet](https://cryptography.io/en/latest/fernet/)), re-keyable for clean
  ownership handover
- **CPU miner** — like back in the day: your laptop, real hashing, 50 KLEX
  per block
- **P2P sync** — `klex serve` / `klex sync host:port`; peers re-validate every
  block they receive
- **Explorer** — localhost web UI for blocks, addresses, mempool
- **Docker** — node, explorer, and seed services, one `docker compose up`
- **Certificate** — printable paper certificate of genesis with QR
- **Tests** — 49 adversarial tests: tampering, forged signatures,
  double-spends, corrupted files, malicious peers, keystore attacks

## Honest spec

| | |
|---|---|
| Consensus | PoW, KlexHash (double SHA3-256) |
| Block time | 60 s target |
| Supply | 21,000,000 KLEX · 50/block · halving every 210,000 blocks |
| Amounts | whole KLEX (integers) |
| Genesis | fixed timestamp · one message · **zero allocation** |
| Signatures | ML-DSA-44 (NIST FIPS 204) on every transaction |
| Implementation | Python ≥ 3.10 · ~1,400 lines (code) · MIT |
| Ports | explorer + P2P bind to 127.0.0.1 by default |

## Install

```bash
git clone https://github.com/logicbreaks/klex-coin && cd klex-coin
pip install -r requirements.txt
```

Or as a standalone command in an isolated environment
([pipx](https://pipx.pypa.io) — a tool that installs Python CLI apps into their
own venv, so they don't fight each other):

```bash
pipx install .
```

## Quickstart

```bash
klex init          # initialize node — see the genesis message
klex wallet new    # post-quantum keypair → KLEX1… address (set a passphrase!)
klex balance
klex mine          # earn 50 KLEX per block, real PoW · Ctrl-C to stop
klex send KLEX1… 25 --memo "hello world"
klex explore       # http://127.0.0.1:8337
klex verify        # re-validate the entire chain from genesis
```

Data lives in `~/.klex/` (override with `--datadir <path>` — works in any
position — or `KLEX_HOME`). Two machines sync via `klex serve` +
`klex sync host:port`. Wallet handover: create the recipient's keystore,
transfer on-chain, then the owner runs `klex wallet rekey` to set a passphrase
you never knew.

## Docker

```bash
docker compose up --build          # node + explorer (127.0.0.1:8337) + seed
docker compose run node python -m klex mine --blocks 10
```

The chain persists in the `klexdata` volume. The explorer is published on the
host's localhost only; the seed publishes 9333 — expose it deliberately.

## Tests

```bash
python -m unittest discover -s tests -t .
```

49 adversarial tests: tampering, forged signatures, double-spends, corrupted
files, malicious peers, keystore attacks, mempool fee-order cases. CI runs the
suite on Ubuntu, macOS, and Windows (Python 3.10 & 3.12) and builds the Docker
image on every push.

## Threat model (the short version)

Protects against: forged transactions (ML-DSA over canonical bytes), chain
tampering (every block re-verifies), double-spend (sequential nonces, checked
twice), genesis-message rewrites (hash is hard-coded), disk theft of secret
keys (encrypted keystore), corrupted data files (loud, explicit refusal).

Does not protect against: 51% attacks (small network, small hashrate — the
honest fix is more miners, not more code), side-channel attacks on the
reference signing library (v1.2 upgrades to hardened
[liboqs](https://github.com/open-quantum-safe/liboqs)), phishing, weak
passphrases, or bugs in ~1,400 overnight lines. Mitigation: the codebase is
readable in an afternoon, adversarially tested, and exposes no network surface
by default. Full details: [docs/whitepaper.md](docs/whitepaper.md §5).

## Roadmap

1. seed node on a free-tier VPS + public explorer
2. hardened ML-DSA via liboqs; memory element in KlexHash
3. **Rust core (v2)** — one static binary, same chain rules
4. privacy research (stealth addresses) — respecting the Monero bar
5. optional 1:1 wrapped token on an L2 with a small, honest liquidity pool

Project memory and the full extension guide live in
[docs/devlog.md](docs/devlog.md) — read it top-down before hacking.

## License

MIT — take it, fork it, learn from it.

---

*KLEX was issued without sale; it is not a financial product. No sale, no
presale, no returns promised, no names on chain. Value starts at zero and
stays there until people voluntarily decide otherwise.*
