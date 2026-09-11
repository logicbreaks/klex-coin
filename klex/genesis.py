"""Genesis block: the immutable identity of the chain."""

from . import chain, config, crypto


def build_genesis() -> dict:
    payload = {
        "type": "genesis",
        "memo": config.GENESIS_MESSAGE,
        "amount": 0,
        "timestamp": config.GENESIS_TIMESTAMP,
    }
    genesis = {
        "index": 0,
        "prev_hash": config.GENESIS_PREV_HASH,
        "timestamp": config.GENESIS_TIMESTAMP,
        "difficulty": config.GENESIS_DIFFICULTY,
        "tx_root": chain.tx_root([payload]),
        "nonce": config.GENESIS_NONCE,
        "txs": [payload],
    }
    genesis["hash"] = chain.block_hash(genesis)
    return genesis