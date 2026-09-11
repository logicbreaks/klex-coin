# Tutorial 1 — from zero to your first mined block

Time: ~10 minutes (2 of them are mining). Prerequisites: Git and Python 3.10+
— or Docker, that's path C.

## Step 0 — pick your install path

All three give you the same `klex` command. Pick one.

### Path A — virtualenv (recommended)

A [virtual environment](https://docs.python.org/3/library/venv.html) is a
private Python playground for one project — whatever you install into it can't
break your system Python, and vice versa. This is the standard, safest way to
run Python software.

```bash
git clone https://github.com/logicbreaks/klex-coin
cd klex-coin
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install .
```

You are now inside the venv (your prompt usually shows `(.venv)`). The `klex`
command is available; when you're done later, leave with `deactivate`.

> If you ever see `klex: command not found` while the folder has a `.venv` —
> the venv isn't activated. Run the activate line above.

### Path B — pipx (standalone command, no activation)

[pipx](https://pipx.pypa.io) installs a Python CLI app into its own
environment and puts it on your PATH globally — `klex` works from any folder,
no activation, no venv juggling:

```bash
git clone https://github.com/logicbreaks/klex-coin
cd klex-coin
pipx install .
```

Upgrading later: `pipx upgrade klex-coin` (or re-run `pipx install .`).

### Path C — Docker (everything in containers)

[Docker Compose](https://docs.docker.com/compose/) runs pre-defined containers
from one command. The repo ships three: `node` (the chain), `explorer` (web
UI), `seed` (serves blocks to peers). Data persists in the `klexdata` volume.

```bash
git clone https://github.com/logicbreaks/klex-coin
cd klex-coin
docker compose up --build -d        # node initializes, explorer on 127.0.0.1:8337
```

A wallet needs a passphrase; in Docker you provide it as an environment
variable instead of typing it:

```bash
docker compose run -e KLEX_WALLET_PASS=demo node python -m klex wallet new
docker compose run node python -m klex mine --blocks 2
docker compose run node python -m klex verify
```

In this tutorial, commands are written for paths A/B. On Docker, prefix each
`klex …` with `docker compose run node` and use `python -m klex …`.

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
node derives the same hash, so nobody can ever swap the message.

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
| `klex: command not found` | venv not activated — run the activate line from Step 0, or use `python -m klex …` |
| `No module named klex` | you're outside the venv, or `pip install .` was skipped |
| mining takes > 60 s | your machine is slower than the target; Ctrl-C, difficulty adapts after block 10 |
| `passphrases do not match` | the two prompts must match exactly; empty is refused |
| `chain exists but state file missing` | someone deleted `state.json`; restore from backup, then `klex verify` |
| port 8337 busy | `klex explore --port 8400` |

Next: [Tutorial 2 — send and receive KLEX](02-send-and-receive.md)