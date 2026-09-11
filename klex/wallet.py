"""Wallet: ML-DSA (FIPS 204) keypairs, KLEX addresses, encrypted keystore.

KLEX_WALLET_PASS (environment variable) may provide the passphrase for
non-interactive setups (CI, Docker). The keystore file is written 0600.
"""

import getpass
import hashlib
import base64
import json
import os
import time

from cryptography.fernet import Fernet, InvalidToken
from dilithium_py.ml_dsa import ML_DSA_44

from . import crypto

KDF_ITERATIONS = 600_000
KEYSTORE_VERSION = 1


def get_passphrase(prompt: str) -> str:
    env = os.environ.get("KLEX_WALLET_PASS")
    if env:
        return env
    return getpass.getpass(prompt)


def generate_keypair():
    return ML_DSA_44.keygen()


def sign(secret_key: bytes, message: bytes) -> bytes:
    return ML_DSA_44.sign(secret_key, message)


def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    try:
        return ML_DSA_44.verify(public_key, message, signature)
    except Exception:
        return False


def encrypt_secret(secret: bytes, passphrase: str) -> dict:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, KDF_ITERATIONS)
    fernet_key = base64.urlsafe_b64encode(key)
    token = Fernet(fernet_key).encrypt(secret)
    return {
        "salt_b64": crypto.encode_b64(salt),
        "token_b64": token.decode("ascii"),
    }


def decrypt_secret(enc: dict, passphrase: str) -> bytes:
    key = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), crypto.decode_b64(enc["salt_b64"]), KDF_ITERATIONS)
    fernet_key = base64.urlsafe_b64encode(key)
    try:
        return Fernet(fernet_key).decrypt(enc["token_b64"].encode("ascii"))
    except InvalidToken:
        raise ValueError("wrong passphrase or corrupted keystore")


def create_wallet_file(path: str) -> dict:
    env_pass = os.environ.get("KLEX_WALLET_PASS")
    if env_pass:
        passphrase = env_pass
    else:
        passphrase = getpass.getpass("keystore passphrase: ")
        again = getpass.getpass("repeat passphrase: ")
        if passphrase != again or not passphrase:
            raise ValueError("passphrases do not match (or empty)")
    if not passphrase:
        raise ValueError("empty passphrase")
    pubkey, secret = generate_keypair()
    address = crypto.pubkey_to_address(pubkey)
    wallet = {
        "version": KEYSTORE_VERSION,
        "address": address,
        "pubkey_b64": crypto.encode_b64(pubkey),
        "enc": encrypt_secret(secret, passphrase),
        "created": int(time.time()),
    }
    write_wallet(wallet, path)
    return wallet


def write_wallet(wallet: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(wallet, f, indent=2)


def rekey_wallet(path: str, old_passphrase: str, new_passphrase: str) -> dict:
    wallet = load_wallet(path)
    secret = decrypt_secret(wallet["enc"], old_passphrase)
    wallet["enc"] = encrypt_secret(secret, new_passphrase)
    wallet["rekeyed"] = int(time.time())
    write_wallet(wallet, path)
    return wallet


def load_wallet(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def secret_key_from_wallet(wallet: dict, passphrase: str) -> bytes:
    return decrypt_secret(wallet["enc"], passphrase)