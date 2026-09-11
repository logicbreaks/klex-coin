# Tutorial 1 — from zero to your first mined block

Time: ~10 minutes (2 of them are mining).
Video version: [watch the recorded session](https://logicbreaks.github.io/klex-coin/tutorial.html).

## 0. Prerequisites

- Python **3.10 or newer** (`python3 --version`) — or Docker, see the README
- ~50 MB of disk, a normal laptop CPU (this is all a KLEX node needs)

Get the code and install:

```bash
git clone https://github.com/logicbreaks/klex-coin
cd klex-coin
pip install -r requirements.txt
```

Prefer a standalone command on your PATH?

```bash
pipx install .        # pipx: https://pipx.pypa.io — installs the `klex` command in an isolated venv
```

All commands below work with either `python -m klex …` or the installed `klex …`.

## Step 1 — start your node

```bash
klex init
```

Expected output:

```
KLEX node initialized.
genesis hash : e62c84b217ee71ac7a3da19b36545956aa4e16aad1911e7f72f50529925868ee
chain id     : e62c84b217ee71ac
genesis says :
  "KLEX · GENESIS · Built overnight with zero budget and full intent, for the one
   who taught me the future is built, not bought. Fair launch. No premine. Value
   starts at zero — like everything great. — K"
allocation   : zero coins. Fair launch confirmed.
```

What just happened: your node wrote the **genesis block** to `~/.klex/chain.json`.
The message is part of the block, its hash is hard-coded in the software — every
node on earth derives the same hash, so nobody can ever swap the message.

> Where does the data live? `~/.klex/` by default. Use `--datadir <path>` (in
> any position) or `KLEX_HOME` to run several independent nodes — handy later.

## Step 2 — create your wallet

```bash
klex wallet new
```

You'll be asked twice for a **passphrase** — this encrypts the private key on
disk (keystore file mode 0600, PBKDF2 → Fernet). Choose something long; there
is no password reset.

```
wallet created (keystore encrypted, file mode 600)
address : KLEX1evui7b7r2petx4q6neqw256ku274iabgncfd7hi
IMPORTANT: back up this file and your passphrase. No passphrase, no coins.
```

Your address is derived from an **ML-DSA public key** (NIST FIPS 204) — a
post-quantum signature scheme. Back up two things, treat them as one:

1. `~/.klex/wallets/wallet.json` (the encrypted keystore)
2. the passphrase

## Step 3 — check the empty chain

```bash
klex balance     # → 0 KLEX
klex info        # height 0 · supply 0 · difficulty 5
```

Supply 0 is the fair-launch guarantee: the genesis block pays nobody. The only
way coins exist is mining.

## Step 4 — mine your first blocks

```bash
klex mine
```

Your CPU now grinds double-SHA3 (the "KlexHash" PoW). Expect a block every few
seconds on a laptop:

```
block #1 found in 4.4s · +50 KLEX → KLEX1evui7b7… · difficulty 5 · txs 0 (mempool 0)
block #2 found in 2.1s · +50 KLEX → KLEX1evui7b7… · difficulty 5 · txs 0 (mempool 0)
```

`Ctrl-C` stops the miner; nothing is lost. Difficulty retargets every 10 blocks
toward the 60 s target, so blocks may slow down as more hashrate joins.

## Step 5 — trust, but verify

```bash
klex verify
```

```
chain valid · 3 blocks · supply 100 KLEX
```

This re-reads every block from genesis, re-checks every signature and every
proof-of-work. Try to break it first: open `chain.json`, change one number, run
`klex verify` again — it will name the exact block you touched. That's the
whole security model in one experiment.

## Step 6 — look around

```bash
klex explore        # → http://127.0.0.1:8337 (localhost only)
```

Genesis message, blocks, your address. Close it with Ctrl-C.

## Troubleshooting

| Problem | Meaning |
|---|---|
| `klex: command not found` | use `python -m klex …` or install with pipx |
| mining takes > 60 s | your machine is slower than the target; Ctrl-C, difficulty adapts after block 10 |
| `passphrases do not match` | the two prompts must match exactly; empty is refused |
| `chain exists but state file missing` | someone deleted `state.json`; restore from backup, then `klex verify` |
| port 8337 busy | `klex explore --port 8400` |

## Recorded session

The complete session above was recorded live (mining at real difficulty):
[player page](https://logicbreaks.github.io/klex-coin/tutorial.html) ·
[raw .cast file](https://github.com/logicbreaks/klex-coin/tree/main/site/casts)

Next: [Tutorial 2 — send and receive KLEX](02-send-and-receive.md)