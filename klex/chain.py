"""Blockchain: blocks, consensus rules, state application, full verification.

Pure functions only; persistence lives in node.py. All amounts are whole KLEX.
"""

import time

from . import config, crypto, tx

COINBASE = "COINBASE"


def block_reward(height: int) -> int:
    halvings = height // config.HALVING_INTERVAL
    return max(config.BLOCK_REWARD >> halvings, 0)


def make_coinbase(miner_addr: str, height: int, fees: int, timestamp: int) -> dict:
    return {
        "type": "coinbase",
        "to": miner_addr,
        "amount": block_reward(height) + fees,
        "fee": 0,
        "nonce": height,
        "timestamp": timestamp,
        "memo": "",
    }


def header_of(block: dict) -> dict:
    return {
        "index": block["index"],
        "prev_hash": block["prev_hash"],
        "timestamp": block["timestamp"],
        "difficulty": block["difficulty"],
        "tx_root": block["tx_root"],
        "nonce": block["nonce"],
    }


def tx_root(txs: list) -> str:
    return crypto.obj_hash(txs)


def block_hash(block: dict) -> str:
    return crypto.block_pow_hash(header_of(block))


def initial_state() -> dict:
    return {
        "balances": {},
        "nonces": {},
        "height": 0,
        "difficulty": config.GENESIS_DIFFICULTY,
        "supply": 0,
    }


def expected_difficulty(blocks: list, height: int) -> int:
    prev = blocks[-1]
    if height % config.RETARGET_INTERVAL != 0:
        return prev["difficulty"]
    anchor_index = height - config.RETARGET_INTERVAL
    if anchor_index < 0 or len(blocks) <= anchor_index:
        return prev["difficulty"]
    anchor = blocks[anchor_index]
    elapsed = prev["timestamp"] - anchor["timestamp"]
    blocks_in_window = config.RETARGET_INTERVAL - 1
    expected = blocks_in_window * config.BLOCK_TIME
    if elapsed <= 0:
        new_diff = prev["difficulty"] + 2
    else:
        ratio = expected / elapsed
        new_diff = round(prev["difficulty"] * ratio)
    new_diff = max(new_diff, prev["difficulty"] - 2)
    new_diff = min(new_diff, prev["difficulty"] + 2)
    return max(min(new_diff, config.MAX_DIFFICULTY), config.MIN_DIFFICULTY)


def validate_block(block: dict, blocks: list, state: dict) -> dict:
    if not isinstance(block, dict):
        raise ValueError("block is not an object")
    required = ("index", "prev_hash", "timestamp", "difficulty", "tx_root", "nonce", "txs")
    missing = [k for k in required if k not in block]
    if missing:
        raise ValueError(f"missing block fields: {missing}")
    prev = blocks[-1]
    height = block["index"]
    if height != prev["index"] + 1:
        raise ValueError(f"bad index {height} after height {prev['index']}")
    if block["prev_hash"] != block_hash(prev):
        raise ValueError("prev_hash does not link to previous block")
    if block["difficulty"] != expected_difficulty(blocks, height):
        raise ValueError(
            f"difficulty {block['difficulty']} != expected {expected_difficulty(blocks, height)}"
        )
    if not isinstance(block["timestamp"], int):
        raise ValueError("timestamp must be an integer")
    if block["timestamp"] <= prev["timestamp"]:
        raise ValueError("timestamp must be greater than previous block")
    if block["timestamp"] > time.time() + 120:
        raise ValueError("timestamp too far in the future")

    txs = block["txs"]
    if not isinstance(txs, list) or not txs:
        raise ValueError("block has no transactions")
    if len(txs) > config.MAX_TXS_PER_BLOCK:
        raise ValueError("too many transactions in block")
    if txs[0].get("type") != "coinbase":
        raise ValueError("first tx must be coinbase")
    if any(t.get("type") == "coinbase" for t in txs[1:]):
        raise ValueError("multiple coinbase txs")
    fees = sum(t.get("fee", 0) for t in txs[1:])
    coinbase = txs[0]
    if coinbase["amount"] != block_reward(height) + fees:
        raise ValueError("coinbase amount does not match reward + fees")
    if coinbase.get("fee", 0) != 0:
        raise ValueError("coinbase fee must be zero")
    if coinbase["timestamp"] != block["timestamp"]:
        raise ValueError("coinbase timestamp must equal block timestamp")
    if not crypto.address_is_valid(coinbase["to"]):
        raise ValueError("coinbase recipient invalid")
    if block["tx_root"] != tx_root(txs):
        raise ValueError("tx_root mismatch")
    pow_hash = block_hash(block)
    if not crypto.meets_target(pow_hash, block["difficulty"]):
        raise ValueError(f"proof-of-work invalid for difficulty {block['difficulty']}")
    if "hash" in block and block["hash"] != pow_hash:
        raise ValueError("stored hash does not match computed hash")

    balances, nonces = dict(state["balances"]), dict(state["nonces"])
    for t in txs[1:]:
        tx.validate(t, balances, nonces)
        tx.apply(t, balances, nonces)
    balances[coinbase["to"]] = balances.get(coinbase["to"], 0) + coinbase["amount"]
    supply = state["supply"] + coinbase["amount"]
    if supply > config.MAX_SUPPLY:
        raise ValueError("supply cap exceeded")
    return {
        "balances": balances,
        "nonces": nonces,
        "height": height,
        "difficulty": block["difficulty"],
        "supply": supply,
    }


def validate_genesis(genesis: dict) -> None:
    if genesis["index"] != 0:
        raise ValueError("genesis index must be 0")
    if genesis["prev_hash"] != config.GENESIS_PREV_HASH:
        raise ValueError("genesis prev_hash must be all zeros")
    if genesis["difficulty"] != config.GENESIS_DIFFICULTY:
        raise ValueError("genesis difficulty mismatch")
    if genesis["timestamp"] != config.GENESIS_TIMESTAMP:
        raise ValueError("genesis timestamp mismatch")
    txs = genesis["txs"]
    if len(txs) != 1 or txs[0].get("type") != "genesis":
        raise ValueError("genesis must carry exactly one genesis payload")
    if txs[0].get("memo") != config.GENESIS_MESSAGE:
        raise ValueError("genesis message mismatch")
    if txs[0].get("amount", 0) != 0:
        raise ValueError("genesis must allocate zero coins")
    if genesis["tx_root"] != tx_root(txs):
        raise ValueError("genesis tx_root mismatch")
    stored = genesis.get("hash", block_hash(genesis))
    if crypto.EXPECTED_GENESIS_HASH and stored != crypto.EXPECTED_GENESIS_HASH:
        raise ValueError("genesis hash does not match the hard-coded chain identity")


def build_block(blocks: list, state: dict, transfers: list, miner_addr: str) -> dict:
    prev = blocks[-1]
    height = prev["index"] + 1
    if len(transfers) > config.MAX_TXS_PER_BLOCK - 1:
        transfers = transfers[: config.MAX_TXS_PER_BLOCK - 1]
    balances, nonces = dict(state["balances"]), dict(state["nonces"])
    validated = []
    fees = 0
    for t in transfers:
        tx.validate(t, balances, nonces)
        tx.apply(t, balances, nonces)
        fees += t["fee"]
        validated.append(t)
    timestamp = max(int(time.time()), prev["timestamp"] + 1)
    coinbase = make_coinbase(miner_addr, height, fees, timestamp)
    full_txs = [coinbase] + validated
    block = {
        "index": height,
        "prev_hash": block_hash(prev),
        "timestamp": timestamp,
        "difficulty": expected_difficulty(blocks, height),
        "tx_root": tx_root(full_txs),
        "nonce": 0,
        "txs": full_txs,
    }
    return block