# KLEX

[![ci](https://github.com/logicbreaks/klex-coin/actions/workflows/ci.yml/badge.svg)](https://github.com/logicbreaks/klex-coin/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

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

> "Built overnight with zero budget and full intent, for the one who taught me
> the future is built, not bought. Fair launch. No premine. Value starts at
> zero — like everything great. — K"

**Your own blockchain. Mineable on a laptop. Ready for the quantum age.**

Three things make KLEX different from the token spam you've seen:

1. **It's not a token.** KLEX is a *chain* — its own ledger, its own rules, ~1,400 lines of readable Python in this very repo. When you can read it, you own it.
2. **Post-quantum by default.** Every transaction is signed with [ML-DSA, NIST FIPS 204](https://csrc.nist.gov/pubs/fips/204/final) — the signature scheme built to survive quantum computers. Old coins will migrate someday. KLEX never had to.
3. **Honest fair launch.** The genesis block pays *nobody*. Coins exist only because someone mined them. Value starts at **zero** — like everything great.

Genesis block hash (hard-coded chain identity):
`e62c84b217ee71ac7a3da19b36545956aa4e16aad1911e7f72f50529925868ee`

> "Built overnight with zero budget and full intent, for the one who taught me
> the future is built, not bought. Fair launch. No premine. Value starts at
> zero — like everything great. — K"

---

## 30 seconds to your first block

```bash
git clone https://github.com/logicbreaks/klex-coin && cd klex-coin
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install .
klex init          # your node + the genesis message
klex wallet new    # post-quantum keypair → your KLEX1… address
klex mine          # real CPU proof-of-work · 50 KLEX per block
klex verify        # re-validate the whole chain, live
```

Mining a block takes a laptop a few seconds. That's the honest sound of proof-of-work.

## Learn it in three tutorials

| | What you do |
|---|---|
| [1 — first block](docs/tutorials/01-first-block.md) | pick your install path (venv / pipx / Docker) → node → wallet → mining → verification |
| [2 — send & receive](docs/tutorials/02-send-and-receive.md) | second wallet → signed transfer → fees & mempool → balances → attack it yourself |

## What's inside

```bash
klex init      klex wallet new      klex mine
klex send KLEX1… 25 --memo "hi"          # quantum-safe signature on every tx
klex explore   # localhost block explorer
klex serve     klex sync host:port       # two nodes, peer-to-peer
```

<details>
<summary><b>Specs</b> — 60 s blocks · KlexHash (double SHA-3) · 21M cap · halving every 210k · whole KLEX · ports on 127.0.0.1</summary>

| | |
|---|---|
| Consensus | PoW — KlexHash (double SHA3-256) |
| Block time | 60 s target, retargets every 10 blocks |
| Supply | 21,000,000 KLEX · 50 per block · halving every 210,000 |
| Genesis | fixed timestamp · one message · **zero allocation** |
| Signatures | ML-DSA-44 (NIST FIPS 204) on every transaction |
| Implementation | Python ≥ 3.10 · MIT · explorer/P2P bind localhost only |

</details>

<details>
<summary><b>Runs everywhere</b> — three operating systems proven in CI, plus Docker</summary>

Test matrix on every push: **Ubuntu · macOS · Windows**, Python 3.10 & 3.12,
plus a full Docker build. Or bring your own container:

```bash
docker compose up --build     # node + explorer (127.0.0.1:8337) + seed
```

</details>

<details>
<summary><b>Security — what it protects, what it doesn't</b></summary>

Protects against: forged transactions (ML-DSA over canonical bytes), chain
tampering (every block re-verifies), double-spend (sequential nonces, checked
twice), genesis rewrites (hash is hard-coded), disk theft of keys (encrypted
keystore), corrupted data (loud refusal).

Does **not** protect against: 51% attacks (small chain = small hashrate —
the honest fix is more miners), side-channel attacks on the reference signing
library (hardened [liboqs](https://github.com/open-quantum-safe/liboqs) is the
v1.2 upgrade), phishing, or weak passphrases.

49 adversarial tests cover the classic attacks — tampering, forgery,
double-spends, corrupted files, malicious peers. See the
[whitepaper threat model](docs/whitepaper.md#5-what-the-security-model-protects--and-what-it-does-not).

</details>

## The map

- [Whitepaper](docs/whitepaper.md) — design, threat model, roadmap
- [Tutorials](docs/tutorials/01-first-block.md) — written walkthroughs
- [Project devlog](docs/devlog.md) — every decision, extension guide for v2
- [Site](https://logicbreaks.github.io/klex-coin/) — plain-words intro

---

*KLEX was issued without sale; it is not a financial product. No presale, no
returns promised, no names on chain. Value starts at zero and stays there
until people voluntarily decide otherwise.*