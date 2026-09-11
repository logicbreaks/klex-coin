"""Transactions: account model, ML-DSA signatures, canonical hashing."""

import time

from . import config, crypto, wallet

TYPES = ("transfer",)


def build_transfer(from_addr: str, to_addr: str, amount: int, nonce: int, fee: int = 0, memo: str = "") -> dict:
    if not crypto.address_is_valid(from_addr):
        raise ValueError("invalid sender address")
    if not crypto.address_is_valid(to_addr):
        raise ValueError("invalid recipient address")
    if not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive integer")
    if not isinstance(fee, int) or not (config.MIN_FEE <= fee <= config.MAX_FEE):
        raise ValueError("fee out of range")
    if not isinstance(nonce, int) or nonce <= 0:
        raise ValueError("nonce must be a positive integer")
    memo = memo or ""
    if len(memo) > config.MAX_MEMO_LEN:
        raise ValueError(f"memo too long (max {config.MAX_MEMO_LEN} chars)")
    return {
        "type": "transfer",
        "from": from_addr,
        "to": to_addr,
        "amount": amount,
        "fee": fee,
        "nonce": nonce,
        "timestamp": int(time.time()),
        "memo": memo,
    }


def signing_payload(tx: dict) -> bytes:
    unsigned = {k: v for k, v in tx.items() if k not in ("pubkey_b64", "sig_b64")}
    return crypto.canonical(unsigned)


def sign_transfer(tx: dict, pubkey: bytes, secret_key: bytes) -> dict:
    signed = dict(tx)
    signed["pubkey_b64"] = crypto.encode_b64(pubkey)
    signed["sig_b64"] = crypto.encode_b64(wallet.sign(secret_key, signing_payload(tx)))
    return signed


def structural_check(tx: dict) -> None:
    if not isinstance(tx, dict):
        raise ValueError("tx is not an object")
    if tx.get("type") != "transfer":
        raise ValueError(f"unsupported tx type: {tx.get('type')!r}")
    required = ("from", "to", "amount", "fee", "nonce", "timestamp", "memo", "pubkey_b64", "sig_b64")
    missing = [k for k in required if k not in tx]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    if not isinstance(tx["amount"], int) or tx["amount"] <= 0:
        raise ValueError("amount must be a positive integer")
    if not isinstance(tx["fee"], int) or tx["fee"] < 0:
        raise ValueError("fee must be a non-negative integer")
    if not isinstance(tx["nonce"], int) or tx["nonce"] <= 0:
        raise ValueError("nonce must be a positive integer")
    if not isinstance(tx["memo"], str) or len(tx["memo"]) > config.MAX_MEMO_LEN:
        raise ValueError("memo invalid or too long")
    if len(tx["memo"]) > config.MAX_MEMO_LEN:
        raise ValueError("memo too long")


def tx_hash(tx: dict) -> str:
    return crypto.obj_hash(tx)


def validate(tx: dict, balances: dict, nonces: dict) -> None:
    structural_check(tx)
    try:
        pubkey = crypto.decode_b64(tx["pubkey_b64"])
        sig = crypto.decode_b64(tx["sig_b64"])
    except Exception as exc:
        raise ValueError("pubkey/sig not valid base64") from exc
    if crypto.pubkey_to_address(pubkey) != tx["from"]:
        raise ValueError("pubkey does not match sender address")
    if not wallet.verify(pubkey, signing_payload(tx), sig):
        raise ValueError("invalid ML-DSA signature")
    if crypto.address_is_valid(tx["to"]) is False:
        raise ValueError("invalid recipient address")
    sender_balance = balances.get(tx["from"], 0)
    if tx["amount"] + tx["fee"] > sender_balance:
        raise ValueError(
            f"insufficient balance: needs {tx['amount'] + tx['fee']}, has {sender_balance}"
        )
    if nonces.get(tx["from"], 0) + 1 != tx["nonce"]:
        raise ValueError(
            f"bad nonce: expected {nonces.get(tx['from'], 0) + 1}, got {tx['nonce']}"
        )


def apply(tx: dict, balances: dict, nonces: dict) -> None:
    balances[tx["from"]] = balances.get(tx["from"], 0) - tx["amount"] - tx["fee"]
    balances[tx["to"]] = balances.get(tx["to"], 0) + tx["amount"]
    nonces[tx["from"]] = tx["nonce"]