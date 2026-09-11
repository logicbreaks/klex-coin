# Tutorial 2 — send and receive KLEX

Time: ~10 minutes. Prerequisite: [Tutorial 1](01-first-block.md) — you have a
node with a funded wallet (any install path).

## What you'll build

Two wallets, one signed transfer between them, mined into a block — and one
experiment in ownership: after the receiver holds the keys, the sender has no
way back. That's not a UX flaw, that's the point.

## Step 1 — create the recipient's wallet

A keystore is just a file of keys, so it can live in its own directory —
independent of any chain:

```bash
klex --datadir ~/.klex-boss wallet new
```

```
address : KLEX1citgyx47huwj75cxwblgo7j6pnyqggkr4thszsa
```

Keep the address handy:

```bash
klex --datadir ~/.klex-boss wallet show
```

> A `--datadir` wallet directory doesn't need `init` — it holds keys, not a
> chain. This separation is also how you hand full ownership to someone later:
> the file moves to their machine and they re-encrypt it with a passphrase of
> their own (`klex wallet rekey`), and from that moment only they can sign.

## Step 2 — send

```bash
klex send KLEX1citgy… 25 --memo "hello world"
```

The CLI asks for your keystore passphrase, signs the transfer locally with your
ML-DSA key (nothing ever leaves the machine), and puts it in the mempool:

```
tx submitted  4061807c802f0093d9167ca5191e1fb1a8cdfc2b8970988544422ee876dcec19
25 KLEX → KLEX1citgy…  memo: hello world
it will be included when the next block is mined
```

Queue another one — mempool accepts several pending transfers per sender:

```bash
klex send KLEX1citgy… 7 --fee 1
```

The fee (whole KLEX) goes to whoever mines the block; fees above 0 get mined
first.

## Step 3 — mine them into a block

```bash
klex mine --blocks 1
```

```
block #3 found in 1.8s · +50 KLEX → KLEX1evui7b7… · difficulty 5 · txs 2 (mempool 0)
```

Both transfers are now in the chain, fee-priority order, with sequential
nonces. Your node earns the 50 block reward plus the 1 fee.

## Step 4 — check both sides

```bash
klex balance                        # your wallet
klex balance KLEX1citgy…            # recipient — 32 KLEX
klex verify                         # full chain re-validation
```

## Step 5 — what a forger would see

Try to spend coins you don't own: create a second wallet, sign a transfer from
*its* address claiming to be you — or hand-edit an amount in `chain.json`.
Every attempt dies in one of two places: at submission (signature/address
mismatch) or at `klex verify` (hash mismatch names the block). The
[attack-vector test suite](https://github.com/logicbreaks/klex-coin/tree/main/tests)
automates exactly these.

## Two nodes talking (optional)

Run a peer on the same machine to see sync happen:

```bash
# terminal A — serve your chain
klex serve --port 9333

# terminal B — a fresh node pulls and validates your blocks
KLEX_HOME=~/.klex-peer klex init
KLEX_HOME=~/.klex-peer klex sync 127.0.0.1:9333
KLEX_HOME=~/.klex-peer klex verify
```

Every block the peer receives is re-validated on arrival; an invalid block is
rejected and the local height stays put. (v1 note: the server serves its
in-memory chain — restart `serve` after mining. On the devlog roadmap.)

## Troubleshooting

| Problem | Meaning |
|---|---|
| `error: wrong passphrase or corrupted keystore` | wrong passphrase; the file can't be opened |
| `insufficient balance` | amount + fee > your balance |
| `bad nonce: expected N` | your pending tx wasn't mined yet; send after the next block |
| `insufficient balance` but it looks funded | a pending transfer already earmarked those coins |
| `duplicate transaction already in mempool` | exactly what it says — it's queued |

Back: [Tutorial 1 — first block](01-first-block.md)