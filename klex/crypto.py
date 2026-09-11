"""Hashing, canonical serialization, proof-of-work, addresses."""

import base64
import hashlib
import json
import re

ADDR_PREFIX = "KLEX1"
_B32 = "abcdefghijklmnopqrstuvwxyz234567"
_ADDR_RE = re.compile(r"^KLEX1[a-z2-7]{38,44}$")

EXPECTED_GENESIS_HASH = "e62c84b217ee71ac7a3da19b36545956aa4e16aad1911e7f72f50529925868ee"


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha3(data: bytes) -> bytes:
    return hashlib.sha3_256(data).digest()


def khash(data: bytes) -> str:
    """KlexHash: double SHA3-256, the proof-of-work function."""
    return hashlib.sha3_256(hashlib.sha3_256(data).digest()).hexdigest()


def obj_hash(obj) -> str:
    return khash(canonical(obj))


def encode_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def decode_b64(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"), validate=True)


def pubkey_hash(pubkey: bytes) -> bytes:
    return sha3(pubkey)[:20]


def make_address(pubkey: bytes) -> str:
    payload = pubkey_hash(pubkey)
    checksum = sha3(b"KLEXCHK" + payload)[:4]
    body = base64.b32encode(payload + checksum).decode("ascii").rstrip("=").lower()
    return ADDR_PREFIX + body


def address_is_valid(address: str) -> bool:
    if not _ADDR_RE.match(address or ""):
        return False
    try:
        raw = base64.b32decode(address[len(ADDR_PREFIX):].upper() + "=" * ((-len(address[len(ADDR_PREFIX):])) % 8))
    except Exception:
        return False
    payload, checksum = raw[:20], raw[20:24]
    return sha3(b"KLEXCHK" + payload)[:4] == checksum


def pubkey_to_address(pubkey: bytes) -> str:
    return make_address(pubkey)


def meets_target(pow_hash: str, difficulty: int) -> bool:
    return pow_hash.startswith("0" * difficulty)


def block_pow_hash(header: dict) -> str:
    return khash(canonical(header))