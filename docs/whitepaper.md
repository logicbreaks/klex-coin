# KLEX Whitepaper · v1.0

*A post-quantum, fair-launch proof-of-work coin.*

---

## 1. What KLEX is

KLEX is a small, complete, self-owned cryptocurrency: a proof-of-work blockchain with
post-quantum signatures, a command-line wallet, a CPU miner, a local block explorer,
peer-to-peer block sync, and a printable certificate of genesis.

It was built from scratch, overnight, on a zero budget — and it is a real
network, not a simulation. The chain starts at exactly zero value
and zero premine. If it ever has value, that value comes only from people
voluntarily using it. That is the point, not a defect.

## 2. Design at a glance

| Parameter | Value |
|---|---|
| Consensus | Proof of work — **KlexHash** (double SHA3-256) |
| Block time | 60 seconds target |
| Difficulty | Starts at 5 leading hex zeros; retargets every 10 blocks (±2 per step, clamped 3–8) |
| Signatures | **ML-DSA** — NIST FIPS 204 (CRYSTALS-Dilithium family) |
| Transaction model | Account-based, sequential nonces, whole-KLEX amounts |
| Supply | 21,000,000 KLEX · 50 per block · halving every 210,000 blocks |
| Genesis | Fixed timestamp · carries the founding message · allocates **zero** coins |
| Implementation | ~1,400 lines of readable Python · MIT licensed |

The genesis block hash is hard-coded into the node software as the chain's
identity:

```
e62c84b217ee71ac7a3da19b36545956aa4e16aad1911e7f72f50529925868ee
```

Anyone can re-derive it from the constants in `klex/config.py`. Editing the
message changes the hash and breaks every node — the founding words are
consensus-critical.

## 3. Why post-quantum signatures

Every transaction in KLEX is signed with **ML-DSA (FIPS 204)**, the NIST
standard for Module-Lattice-Based Digital Signatures finalized in 2024.
Classical schemes (ECDSA, Ed25519) are believed to fall to a sufficiently large
quantum computer via Shor's algorithm; ML-DSA is designed to resist quantum
attacks. Hashing with SHA-3 and double-SHA3 for proof-of-work keeps the rest of
the stack in the same spirit (SHA-2 is only weakened by Grover; SHA-3 at 256
bits keeps a comfortable margin).

The ML-DSA signatures are ~2.4 KB and the pure-Python signing costs ~30–60 ms.
That is the honest price of quantum resistance, and at this scale it is fine.

## 4. Fair launch, stated precisely

- The genesis block contains exactly one payload: the founding message.
  It pays zero coins to anyone.
- The only way KLEX is ever created is by mining blocks. Block #1 belongs to
  whoever computes the first valid proof-of-work.
- There is no ICO, no presale, no team allocation, no VC round, and no promise
  of returns — ever. KLEX is issued without sale and runs as an experiment.
- Market value starts at zero and stays there until real people decide
  otherwise, in voluntary trades. Nothing in KLEX exists to pump it.

## 5. What the security model protects — and what it does not

**Protects against:**
- Forged transactions (ML-DSA signatures over canonical bytes; pubkey must
  derive to the sender address)
- Chain tampering (every block hash links and re-verifies; `klex verify`
  re-validates the whole chain from genesis in seconds)
- Double-spending (account nonces enforced sequentially, checked at
  submission and again at block assembly)
- Message rewriting (genesis hash is hard-coded; the founding message is
  effectively immutable)
- Key theft from disk (keystore is encrypted with Fernet; PBKDF2-HMAC-SHA256,
  600,000 iterations)

**Does not protect against:**
- **51% attacks.** A tiny network has tiny total hashrate. This is true of
  Bitcoin's first months too. KLEX is honest about it: consensus security grows
  with the number of independent miners, not with the codebase.
- Side-channel attacks on the signing library. `dilithium-py` is a clean-room
  reference implementation that passes all NIST test vectors but is not
  constant-time. The upgrade path is `liboqs` (Open Quantum Safe) —
  same signatures, hardened implementation. Planned for v2.
- Social attacks: phishing, passphrase theft, someone stealing your printed
  certificate. Keys are only as safe as where you keep them.
- Bugs in 1,400 lines written overnight. Mitigation: the codebase is small
  enough to read in an afternoon, ships with a test suite covering the
  classic failure modes, and has no network surface by default (explorer and
  P2P bind to localhost only).

## 6. Roadmap (in order of honesty, not hype)

1. **v1.1 — uptime**: one seed node on a free-tier VPS; explorer deployed;
   peers can `klex sync`.
2. **v1.2 — hardening**: liboqs-based ML-DSA (side-channel hardened), memory
   element in KlexHash, multi-core miner.
3. **v2 — Rust core**: a single static binary node, same chain rules. Rust was
   chosen for v2 the way one chooses a language: it is the one he always said
   would take over.
4. **Privacy layer** (research): stealth addresses are the plausible next step;
   ring signatures are heavier. Monero set the bar here and it is respected.
5. **Wrapped KLEX** (optional): a 1:1 bridge token on an L2 with a small,
   honest liquidity pool — only ever marketed as an experiment, never as an
   investment.

## 7. Legal and ethical notes

KLEX is given, not sold. Nothing here is investment advice, no return is
promised or implied, and no personal names are embedded in the chain. If you
received KLEX as a gift, treat it as a gift: interesting technology, uncertain
value, zero obligations in either direction.

---

*Genesis message, permanently:*

> "KLEX · GENESIS · Built overnight with zero budget and full intent, for the one
> who taught me the future is built, not bought. Fair launch. No premine. Value
> starts at zero — like everything great. — K"