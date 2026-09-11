"""Node-level behaviour: mempool lifecycle, history, info."""

import unittest

from klex import chain

from tests.helpers import cleanup_node, fast_mode, make_node, make_wallet, transfer


class TestNode(unittest.TestCase):
    def setUp(self):
        fast_mode()
        self.node = make_node()
        self.alice = make_wallet()
        self.bob = make_wallet()

    def tearDown(self):
        cleanup_node(self.node)

    def test_duplicate_tx_rejected(self):
        self.node.mine_block(self.alice["address"])
        signed = transfer(self.alice, self.bob["address"], 3, nonce=1)
        self.node.submit_transfer(signed)
        with self.assertRaises(ValueError):
            self.node.submit_transfer(signed)

    def test_mempool_cleared_after_mine(self):
        self.node.mine_block(self.alice["address"])
        self.node.submit_transfer(transfer(self.alice, self.bob["address"], 3, nonce=1))
        self.assertEqual(len(self.node.mempool), 1)
        self.node.mine_block(self.bob["address"])
        self.assertEqual(len(self.node.mempool), 0)
        self.assertEqual(self.node.balance(self.bob["address"]), 3 + chain.block_reward(2))

    def test_address_history(self):
        self.node.mine_block(self.alice["address"])
        self.node.submit_transfer(transfer(self.alice, self.bob["address"], 3, nonce=1, memo="hey"))
        self.node.mine_block(self.bob["address"])
        alice_hist = self.node.address_history(self.alice["address"])
        bob_hist = self.node.address_history(self.bob["address"])
        self.assertEqual(len(alice_hist), 2)
        self.assertEqual(len(bob_hist), 2)
        memos = [h["tx"].get("memo", "") for h in bob_hist]
        self.assertIn("hey", memos)

    def test_info_shape(self):
        info = self.node.info()
        self.assertTrue(info["initialized"])
        self.assertEqual(info["height"], 0)
        self.assertEqual(info["supply"], 0)
        self.assertEqual(info["genesis_hash"], self.node.blocks[0]["hash"])

    def test_reward_halving_math(self):
        self.assertEqual(chain.block_reward(0), 50)
        self.assertEqual(chain.block_reward(209_999), 50)
        self.assertEqual(chain.block_reward(210_000), 25)
        self.assertEqual(chain.block_reward(420_000), 12)


    def test_multi_pending_with_fees_all_mined(self):
        self.node.mine_block(self.alice["address"])
        carol = make_wallet()
        low_fee_first = transfer(self.alice, carol["address"], 5, nonce=1, fee=0)
        high_fee_second = transfer(self.alice, carol["address"], 3, nonce=2, fee=1)
        self.node.submit_transfer(low_fee_first)
        self.node.submit_transfer(high_fee_second)
        self.node.mine_block(self.bob["address"])
        self.assertEqual(self.node.balance(carol["address"]), 8)
        self.assertEqual(
            self.node.balance(self.alice["address"]),
            chain.block_reward(1) - 5 - 3 - 1,
        )
        self.assertTrue(self.node.verify()["ok"])

    def test_high_fee_pending_does_not_drop_valid_tx(self):
        self.node.mine_block(self.alice["address"])
        carol, dave = make_wallet(), make_wallet()
        first = transfer(self.alice, carol["address"], 5, nonce=1, fee=0)
        second = transfer(self.alice, dave["address"], 3, nonce=2, fee=2)
        self.node.submit_transfer(first)
        self.node.submit_transfer(second)
        self.node.mine_block(self.bob["address"])
        self.assertEqual(self.node.balance(carol["address"]), 5)
        self.assertEqual(self.node.balance(dave["address"]), 3)
        self.assertEqual(len(self.node.mempool), 0)


if __name__ == "__main__":
    unittest.main()