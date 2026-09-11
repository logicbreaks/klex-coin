# TODO

Deferred work, newest intent on top. Nothing here is a promise of a date.

- [ ] **Recorded demo sessions** (asciinema) + embedded players/SVGs on the site and README — scripts and player page are ready; recordings postponed for time reasons
- [ ] **Security audit step** — guided adversarial review of the full codebase (manual + automated), documented threat-model sign-off
- [ ] v1.1: seed node on a free-tier VPS; public explorer behind a reverse proxy; `serve` re-reads chain.json per request (staleness fix)
- [ ] v1.1: Docker smoke test on a real daemon; rootless compose hardening
- [ ] v1.2: hardened ML-DSA via [liboqs](https://github.com/open-quantum-safe/liboqs); memory element in KlexHash; multi-core miner
- [ ] v1.2: SQLite state backend; streaming `verify`
- [ ] v2: Rust core — one static binary, same consensus rules
- [ ] research: stealth addresses (privacy), respecting the Monero bar
- [ ] optional: 1:1 wrapped KLEX on an L2 with a small, honest liquidity pool