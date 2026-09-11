"""Shared test helpers: fast difficulty, throwaway wallets, temp nodes."""

import os
import shutil
import tempfile

from klex import config, crypto, node as node_mod, tx as tx_mod, wallet as wallet_mod


def fast_mode():
    """Reduce difficulty for tests; genesis identity check is disabled."""
    config.GENESIS_DIFFICULTY = 1
    crypto.EXPECTED_GENESIS_HASH = None


def slow_mode():
    """Restore consensus constants (call in tearDown)."""
    config.GENESIS_DIFFICULTY = 5
    crypto.EXPECTED_GENESIS_HASH = "e62c84b217ee71ac7a3da19b36545956aa4e16aad1911e7f72f50529925868ee"


def make_wallet():
    pubkey, secret = wallet_mod.generate_keypair()
    return {
        "pubkey": pubkey,
        "secret": secret,
        "address": crypto.pubkey_to_address(pubkey),
    }


def make_node(datadir: str = None):
    fast_mode()
    datadir = datadir or tempfile.mkdtemp(prefix="klex-test-")
    n = node_mod.Node(datadir)
    n.init()
    return n


def cleanup_node(n: node_mod.Node):
    slow_mode()
    if os.path.isdir(n.datadir):
        shutil.rmtree(n.datadir, ignore_errors=True)


def transfer(wallet, to_addr, amount, nonce, fee=0, memo=""):
    tx = tx_mod.build_transfer(wallet["address"], to_addr, amount, nonce, fee=fee, memo=memo)
    return tx_mod.sign_transfer(tx, wallet["pubkey"], wallet["secret"])