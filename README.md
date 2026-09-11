# KLEX

[![ci](https://github.com/YOUR-NAME/klex-coin/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-NAME/klex-coin/actions/workflows/ci.yml)

A post-quantum, fair-launch proof-of-work coin, built from scratch as an open experiment.
Runs on Linux, macOS, and Windows (CI proves it on all three), or in Docker.

```
█▀█ █▀▀ █▀█ █▀█ █▀   ▄▄   █▀█ █▀█ █▀
█▀▄ ██▄ █▀▀ █▀▄ ▄█   ░░   █▀▀ █▀▄ ▄█
▀ ▀ ▀▀▀ ▀   ▀ ▀ ▀▀   ▀▀   ▀    ▀   ▀▀
```

> "Built overnight with zero budget and full intent, for the one who taught me
> the future is built, not bought. Fair launch. No premine. Value starts at
> zero — like everything great. — K"

Genesis block hash (hard-coded chain identity):
`e62c84b217ee71ac7a3da19b36545956aa4e16aad1911e7f72f50529925868ee`

---

## What this is

A small but **real** cryptocurrency, complete in one repo:

- **Own blockchain** — blocks, transactions, difficulty retargeting, full
  re-verification (`klex verify` re-validates everything from genesis)
- **Post-quantum signatures** — every transaction is signed with **ML-DSA**
  (NIST FIPS 204, CRYSTALS-Dilithium family), designed to survive quantum
  computers
- **Proof of work** — KlexHash = double SHA3-256, CPU-mined, 60 s block target
- **Wallet** — ML-DSA keypairs, `KLEX1…` addresses with checksums,
  passphrase-encrypted keystore, re-keyable for clean ownership handover
- **CPU miner** — like back in the day: your laptop, real hashing, 50 KLEX
  per block
- **P2P sync** — `klex serve` / `klex sync host:port`; peers re-validate
  every block they receive
- **Explorer** — localhost web UI for blocks, addresses, mempool
- **Docker** — node, explorer, and seed services, one `docker compose up`
- **Certificate** — printable paper certificate of genesis with QR
- **Tests** — 47 adversarial tests: tampering, forged signatures,
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
| Implementation | Python ≥ 3.10 · ~2,000 lines incl. tests · MIT |
| Ports | explorer + P2P bind to 127.0.0.1 by default |

## Install

```bash
git clone https://github.com/YOUR-NAME/klex-coin && cd klex-coin
pip install -r requirements.txt     # or: pipx install . (gives you `klex`)
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

Two machines sync: `klex serve` on one, `klex sync host:port` on the other.
Wallet handover: create the recipient's keystore, transfer on-chain, then the
owner runs `klex wallet rekey` to set a passphrase you never knew.

Data lives in `~/.klex/` (override with `--datadir` or `KLEX_HOME`).

## Docker

```bash
docker compose up --build          # node + explorer (127.0.0.1:8337) + seed
docker compose run node python -m klex mine --blocks 10   # warm-up mining
```

The chain persists in the `klexdata` volume. The explorer is published on the
host's localhost only; the seed publishes 9333 — expose it deliberately.

## Tests

```bash
python -m unittest discover -s tests -t .
```

CI runs the same suite on Ubuntu, macOS, and Windows (Python 3.10 & 3.12) and
builds the Docker image on every push.

## Threat model (the short version)

Protects against: forged transactions (ML-DSA over canonical bytes), chain
tampering (every block re-verifies), double-spend (sequential nonces, checked
twice), genesis-message rewrites (hash is hard-coded), disk theft of secret
keys (encrypted keystore), corrupted data files (loud, explicit refusal).

Does not protect against: 51% attacks (small network, small hashrate — the
honest fix is more miners, not more code), side-channel attacks on the
reference signing library (v1.2 upgrades to hardened liboqs), phishing, weak
passphrases, or bugs in ~2,000 overnight lines. Mitigation: the codebase is
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

MIT — take it, fork it, learn from it. ***REMOVED***


---

*KLEX was issued without sale; it is not a financial product. No sale, no presale, no returns
promised, no names on chain. Value starts at zero and stays there until people
voluntarily decide otherwise.*