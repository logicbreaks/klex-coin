"""Genesis, chain integrity, and consensus-rule tests."""

import unittest

from klex import chain, config, crypto, genesis, miner as miner_mod, tx as tx_mod, wallet as wallet_mod

from tests.helpers import cleanup_node, fast_mode, make_node, make_wallet, transfer


class TestGenesis(unittest.TestCase):
    def test_genesis_deterministic_and_message(self):
        g1 = genesis.build_genesis()
        g2 = genesis.build_genesis()
        self.assertEqual(g1, g2)
        self.assertEqual(g1["txs"][0]["memo"], config.GENESIS_MESSAGE)
        self.assertEqual(g1["txs"][0]["amount"], 0)
        self.assertEqual(g1["txs"][0]["type"], "genesis")
        self.assertIn("no premine", g1["txs"][0]["memo"].lower())

    def test_genesis_validates(self):
        chain.validate_genesis(genesis.build_genesis())

    def test_genesis_message_tamper_detected(self):
        g = genesis.build_genesis()
        g["txs"][0]["memo"] = g["txs"][0]["memo"][:-1] + "?"
        with self.assertRaises(ValueError):
            chain.validate_genesis(g)


class TestChain(unittest.TestCase):
    def setUp(self):
        fast_mode()
        self.node = make_node()
        self.alice = make_wallet()
        self.bob = make_wallet()

    def tearDown(self):
        cleanup_node(self.node)

    def test_mine_and_verify(self):
        self.node.mine_block(self.alice["address"])
        self.node.mine_block(self.alice["address"])
        self.assertEqual(
            self.node.balance(self.alice["address"]),
            chain.block_reward(1) + chain.block_reward(2),
        )
        report = self.node.verify()
        self.assertTrue(report["ok"], report["errors"])

    def test_send_and_mine(self):
        self.node.mine_block(self.alice["address"])
        signed = transfer(self.alice, self.bob["address"], 7, nonce=1, memo="demo")
        h = self.node.submit_transfer(signed)
        self.assertEqual(len(h), 64)
        self.node.mine_block(self.bob["address"])
        self.assertEqual(self.node.balance(self.bob["address"]), 7 + chain.block_reward(2))
        self.assertEqual(self.node.balance(self.alice["address"]), chain.block_reward(1) - 7)
        self.assertTrue(self.node.verify()["ok"])

    def test_tampered_amount_detected(self):
        self.node.mine_block(self.alice["address"])
        self.node.submit_transfer(transfer(self.alice, self.bob["address"], 7, nonce=1))
        self.node.mine_block(self.bob["address"])
        self.node.blocks[-1]["txs"][1]["amount"] = 9999
        self.assertFalse(self.node.verify()["ok"])

    def test_tampered_tx_root_detected(self):
        self.node.mine_block(self.alice["address"])
        self.node.blocks[-1]["tx_root"] = "0" * 64
        self.assertFalse(self.node.verify()["ok"])

    def test_forged_signature_rejected(self):
        self.node.mine_block(self.alice["address"])
        mallory = make_wallet()
        forged = {
            "type": "transfer",
            "from": self.alice["address"],
            "to": mallory["address"],
            "amount": 10,
            "fee": 0,
            "nonce": 1,
            "timestamp": 123,
            "memo": "",
            "pubkey_b64": crypto.encode_b64(mallory["pubkey"]),
        }
        forged["sig_b64"] = crypto.encode_b64(
            wallet_mod.sign(mallory["secret"], tx_mod.signing_payload(forged))
        )
        with self.assertRaises(ValueError):
            self.node.submit_transfer(forged)

    def test_wrong_sender_key_rejected(self):
        self.node.mine_block(self.alice["address"])
        mallory = make_wallet()
        signed = transfer(mallory, self.bob["address"], 10, nonce=1)
        signed["from"] = self.alice["address"]
        signed["pubkey_b64"] = crypto.encode_b64(mallory["pubkey"])
        with self.assertRaises(ValueError):
            self.node.submit_transfer(signed)

    def test_double_spend_same_nonce_rejected(self):
        self.node.mine_block(self.alice["address"])
        carol, dave = make_wallet(), make_wallet()
        self.node.submit_transfer(transfer(self.alice, carol["address"], 5, nonce=1))
        with self.assertRaises(ValueError):
            self.node.submit_transfer(transfer(self.alice, dave["address"], 5, nonce=1))

    def test_two_pending_same_nonce_mine_rejected(self):
        self.node.mine_block(self.alice["address"])
        carol, dave = make_wallet(), make_wallet()
        first = transfer(self.alice, carol["address"], 5, nonce=1)
        self.node.submit_transfer(first)
        self.node.mempool.append(transfer(self.alice, dave["address"], 5, nonce=1))
        with self.assertRaises(ValueError):
            self.node.mine_block(self.bob["address"])

    def test_insufficient_balance_rejected(self):
        broke = make_wallet()
        with self.assertRaises(ValueError):
            self.node.submit_transfer(transfer(broke, self.alice["address"], 5, nonce=1))

    def test_bad_nonce_rejected(self):
        self.node.mine_block(self.alice["address"])
        with self.assertRaises(ValueError):
            self.node.submit_transfer(transfer(self.alice, self.bob["address"], 1, nonce=5))

    def test_invalid_pow_rejected(self):
        self.node.mine_block(self.alice["address"])
        block = chain.build_block(self.node.blocks, self.node.state, [], self.alice["address"])
        if crypto.meets_target(chain.block_hash(block), block["difficulty"]):
            block["nonce"] += 1
        while crypto.meets_target(chain.block_hash(block), block["difficulty"]):
            block["nonce"] += 1
        with self.assertRaises(ValueError):
            self.node.add_block(block)

    def test_timestamp_monotonic(self):
        self.node.mine_block(self.alice["address"])
        first_ts = self.node.blocks[-1]["timestamp"]
        self.node.mine_block(self.alice["address"])
        self.assertGreater(self.node.blocks[-1]["timestamp"], first_ts)

    def test_difficulty_retarget_math(self):
        import time as _t

        now = int(_t.time())
        D = 5
        anchor_ts = now - config.RETARGET_INTERVAL * config.BLOCK_TIME
        window = [dict(self.node.blocks[0], timestamp=anchor_ts)]
        for i in range(1, config.RETARGET_INTERVAL):
            window.append(dict(self.node.blocks[0], timestamp=anchor_ts + i, difficulty=D))
        fast_diff = chain.expected_difficulty(window, config.RETARGET_INTERVAL)
        self.assertGreater(fast_diff, D)

        slow_window = [dict(self.node.blocks[0], timestamp=anchor_ts, difficulty=D)]
        for i in range(1, config.RETARGET_INTERVAL):
            slow_window.append(
                dict(self.node.blocks[0], timestamp=anchor_ts + i * config.BLOCK_TIME * 100, difficulty=D)
            )
        slow_diff = chain.expected_difficulty(slow_window, config.RETARGET_INTERVAL)
        self.assertLess(slow_diff, D)

        ontime = chain.expected_difficulty(
            [dict(self.node.blocks[0], timestamp=anchor_ts - i * config.BLOCK_TIME, difficulty=D) for i in
             range(config.RETARGET_INTERVAL)][::-1],
            config.RETARGET_INTERVAL,
        )
        self.assertEqual(ontime, D)


if __name__ == "__main__":
    unittest.main()