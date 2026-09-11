# KLEX

A post-quantum, fair-launch proof-of-work coin, built from scratch as an open experiment.

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
  (NIST FIPS 204 / CRYSTALS-Dilithium family), the 2024 NIST standard designed
  to survive quantum computers
- **Proof of work** — KlexHash = double SHA3-256, CPU-mined, 60 s block target,
  difficulty retargets every 10 blocks
- **Wallet** — ML-DSA keypairs, `KLEX1…` addresses with checksums,
  passphrase-encrypted keystore (Fernet + PBKDF2, 600k iterations)
- **CPU miner** — like back in the day: your laptop, real hashing, 50 KLEX
  per block
- **Explorer** — localhost web UI for blocks, addresses, mempool
- **P2P sync** — newline-JSON over TCP, manual peers (`klex serve` / `klex sync`)
- **Certificate** — printable paper certificate of genesis with QR of the
  first wallet
- **Test suite** — 32 tests: tampering, forged signatures, double-spends,
  invalid PoW, keystore roundtrips, retarget math

## Honest spec

| | |
|---|---|
| Consensus | PoW, KlexHash (double SHA3-256) |
| Block time | 60 s target |
| Supply | 21,000,000 KLEX · 50/block · halving every 210,000 blocks |
| Amounts | whole KLEX (integers) |
| Genesis | fixed timestamp · one message · **zero allocation** |
| Language | Python ≥ 3.10, ~1,700 lines |
| Network | explorer + P2P bind to 127.0.0.1 only |

## Quickstart

```bash
pip install -r requirements.txt

python -m klex init          # initialize node, see the genesis message
python -m klex wallet new    # create wallet (set a passphrase!)
python -m klex balance
python -m klex mine          # Ctrl-C to stop
python -m klex send KLEX1… 25 --memo "hello world"
python -m klex explore       # http://127.0.0.1:8337
python -m klex verify
```

Data lives in `~/.klex/` (override with `--datadir` or `KLEX_HOME`).
Two machines sync via `klex serve` + `klex sync host:port`.

## Tests

```bash
python -m unittest discover -s tests -t .
```

## Threat model (the short version)

Protects against: forged transactions, chain tampering, double-spend,
genesis-message rewrites, disk theft of secret keys.

Does not protect against: 51% attacks (a small network has a small hashrate —
the honest fix is more miners, not more code), side-channel attacks on the
reference signing library (v1.2 upgrades to hardened liboqs), phishing, or
weak passphrases. Full details: [docs/whitepaper.md](docs/whitepaper.md §5).

## Roadmap

1. seed node on a free-tier VPS + public explorer
2. hardened ML-DSA via liboqs; memory element in KlexHash
3. **Rust core (v2)** — one static binary, same chain rules. Chosen because it
   is the language that (as its future maintainer keeps insisting) will take
   over.
4. privacy research (stealth addresses) — respecting the bar Monero set
5. optional 1:1 wrapped token on an L2 with a small, honest liquidity pool

## License

MIT — take it, fork it, learn from it. ***REMOVED***


---

*KLEX was issued without sale; it is not a financial product. No sale, no presale, no returns
promised, no names on chain. Value starts at zero and stays there until people
voluntarily decide otherwise.*