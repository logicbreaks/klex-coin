"""Adversarial tests: corruption, overflow, protocol abuse, tampering depth."""

import json
import os
import socket
import threading
import unittest

from klex import chain, config, crypto, net, node as node_mod, tx as tx_mod

from tests.helpers import cleanup_node, fast_mode, make_node, make_wallet, transfer


class TestCorruption(unittest.TestCase):
    def setUp(self):
        fast_mode()
        self.node = make_node()
        self.alice = make_wallet()

    def tearDown(self):
        cleanup_node(self.node)

    def test_corrupted_chain_file_detected(self):
        path = self.node.chain_path
        with open(path, "w") as f:
            f.write('{"blocks": [ {"index": 0, "trunc')
        with self.assertRaises(RuntimeError):
            node_mod.Node(self.node.datadir)

    def test_state_file_missing_with_blocks_detected(self):
        os.remove(self.node.state_path)
        with self.assertRaises(RuntimeError):
            node_mod.Node(self.node.datadir)

    def test_tampered_genesis_in_chain_detected(self):
        self.node.blocks[0]["txs"][0]["memo"] += " (edited)"
        with self.assertRaises(ValueError):
            chain.validate_genesis(self.node.blocks[0])

    def test_deep_chain_rewind_detected(self):
        self.node.mine_block(self.alice["address"])
        self.node.mine_block(self.alice["address"])
        self.node.blocks[1]["timestamp"] += 5
        report = self.node.verify()
        self.assertFalse(report["ok"])
        self.assertTrue(any("block 1" in e for e in report["errors"]))

    def test_stored_hash_mismatch_detected(self):
        self.node.mine_block(self.alice["address"])
        self.node.blocks[-1]["hash"] = "f" * 64
        self.assertFalse(self.node.verify()["ok"])


class TestMalformedTransactions(unittest.TestCase):
    def setUp(self):
        fast_mode()
        self.node = make_node()
        self.alice = make_wallet()
        self.node.mine_block(self.alice["address"])

    def tearDown(self):
        cleanup_node(self.node)

    def test_huge_amount_rejected(self):
        with self.assertRaises(ValueError):
            self.node.submit_transfer(
                transfer(self.alice, self.alice["address"], 10**30, nonce=1)
            )

    def test_negative_and_float_amount_rejected(self):
        for bad in (-1, 1.0, "1", None):
            with self.assertRaises(ValueError):
                tx_mod.build_transfer(self.alice["address"], self.alice["address"], bad, 1)

    def test_garbage_base64_rejected(self):
        w = make_wallet()
        tx = tx_mod.build_transfer(self.alice["address"], w["address"], 1, 1)
        tx["pubkey_b64"] = "!!!not-base64!!!"
        tx["sig_b64"] = "%%%also-not%%%"

        import base64 as b64mod

        with self.assertRaises(ValueError):
            b64mod.b64decode(tx["pubkey_b64"], validate=True)
        with self.assertRaises(ValueError):
            self.node.submit_transfer(tx)

    def test_fee_overflow_rejected(self):
        with self.assertRaises(ValueError):
            tx_mod.build_transfer(
                self.alice["address"], self.alice["address"], 1, 1, fee=config.MAX_FEE + 1
            )

    def test_unsupported_tx_type_rejected(self):
        evil = {"type": "print-money", "amount": 1_000_000, "to": self.alice["address"]}
        with self.assertRaises(ValueError):
            tx_mod.structural_check(evil)

    def test_block_with_gap_index_rejected(self):
        block = chain.build_block(self.node.blocks, self.node.state, [], self.alice["address"])
        block["index"] = block["index"] + 7
        from klex import miner as miner_mod

        miner_mod.solve(block)
        with self.assertRaises(ValueError):
            self.node.add_block(block)

    def test_future_timestamp_rejected(self):
        import time as _t

        block = chain.build_block(self.node.blocks, self.node.state, [], self.alice["address"])
        from klex import miner as miner_mod

        block["timestamp"] = int(_t.time()) + 10_000
        block["txs"][0]["timestamp"] = block["timestamp"]
        block["tx_root"] = chain.tx_root(block["txs"])
        from klex import miner as miner_mod

        solved, _ = miner_mod.solve(block)
        with self.assertRaises(ValueError):
            self.node.add_block(solved)

    def test_mempool_cap_enforced(self):
        original_cap = config.MEMPOOL_CAP
        config.MEMPOOL_CAP = 1
        try:
            self.node.mine_block(self.alice["address"])
            self.node.submit_transfer(transfer(self.alice, make_wallet()["address"], 1, nonce=1))
            with self.assertRaises(ValueError):
                self.node.submit_transfer(transfer(self.alice, make_wallet()["address"], 1, nonce=2))
        finally:
            config.MEMPOOL_CAP = original_cap


class TestBlockCapacity(unittest.TestCase):
    def test_block_capped_at_max_txs(self):
        fast_mode()
        node = make_node()
        try:
            alice = make_wallet()
            node.mine_block(alice["address"])
            node.mine_block(alice["address"])
            targets = [make_wallet()["address"] for _ in range(70)]
            for i, to in enumerate(targets):
                node.submit_transfer(transfer(alice, to, 1, nonce=i + 1))
            self.assertEqual(len(node.mempool), 70)
            block = node.mine_block(alice["address"])
            self.assertEqual(len(block["txs"]), config.MAX_TXS_PER_BLOCK)
            self.assertTrue(node.verify()["ok"])
            self.assertLess(len(node.mempool), 70)
        finally:
            cleanup_node(node)


class TestMaliciousPeer(unittest.TestCase):
    def test_sync_rejects_invalid_blocks(self):
        fast_mode()
        victim = make_node()
        try:
            victim.mine_block(make_wallet()["address"])
            victim_height = victim.state["height"]

            def fake_serve(sock):
                conn, _ = sock.accept()
                with conn:
                    conn.recv(65536)
                    fake_blocks = [
                        dict(
                            _GENESIS_LIKE,
                            txs=[dict(_GENESIS_LIKE["txs"][0])],
                        )
                    ]
                    conn.sendall(json.dumps({"cmd": "CHAIN", "blocks": fake_blocks}).encode() + b"\n")

            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            port = srv.getsockname()[1]
            t = threading.Thread(target=fake_serve, args=(srv,), daemon=True)
            t.start()
            with self.assertRaises(ValueError):
                net.sync(victim, f"127.0.0.1:{port}")
            self.assertEqual(victim.state["height"], victim_height)
        finally:
            srv.close()
            cleanup_node(victim)


_GENESIS_LIKE = {
    "index": 0,
    "prev_hash": "0" * 64,
    "timestamp": 0,
    "difficulty": 1,
    "tx_root": "0" * 64,
    "nonce": 0,
    "hash": "0" * 64,
    "txs": [{"type": "genesis", "memo": "fake", "amount": 0, "timestamp": 0}],
}


if __name__ == "__main__":
    unittest.main()