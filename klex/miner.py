"""CPU miner: KlexHash proof-of-work loop.

The hot loop builds the canonical header bytes directly (sorted-key JSON,
same layout as crypto.canonical) and double-SHA3s them; the found nonce is
re-verified through the canonical path before returning.
"""

import hashlib
import time

from . import chain, crypto


def solve(block: dict) -> tuple[dict, float]:
    started = time.time()
    difficulty = block["difficulty"]
    index = block["index"]
    prev_hash = block["prev_hash"]
    timestamp = block["timestamp"]
    tx_root = block["tx_root"]
    nonce = 0
    while True:
        header = (
            f'{{"difficulty":{difficulty},"index":{index},"nonce":{nonce},'
            f'"prev_hash":"{prev_hash}","timestamp":{timestamp},"tx_root":"{tx_root}"}}'
        ).encode("utf-8")
        pow_hash = hashlib.sha3_256(hashlib.sha3_256(header).digest()).hexdigest()
        if pow_hash.startswith("0" * difficulty):
            block["nonce"] = nonce
            assert crypto.block_pow_hash(chain.header_of(block)) == pow_hash, "fast path mismatch"
            block["hash"] = pow_hash
            return block, time.time() - started
        nonce += 1


def hashrate_estimate(difficulty: int, seconds: float) -> float:
    if seconds <= 0:
        return 0.0
    return (16**difficulty) / seconds