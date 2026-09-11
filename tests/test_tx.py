"""Address encoding, keystore encryption, and transaction validation tests."""

import unittest

from klex import crypto, tx as tx_mod, wallet as wallet_mod

from tests.helpers import make_wallet


class TestAddresses(unittest.TestCase):
    def test_roundtrip_and_checksum(self):
        w = make_wallet()
        self.assertTrue(crypto.address_is_valid(w["address"]))
        self.assertEqual(w["address"][:5], "KLEX1")

    def test_typo_rejected(self):
        w = make_wallet()
        addr = w["address"]
        mutated = addr[:-1] + ("a" if addr[-1] != "a" else "b")
        self.assertFalse(crypto.address_is_valid(mutated))

    def test_garbage_rejected(self):
        self.assertFalse(crypto.address_is_valid("KLEX1"))
        self.assertFalse(crypto.address_is_valid("KLEX1" + "0" * 40))
        self.assertFalse(crypto.address_is_valid(""))
        self.assertFalse(crypto.address_is_valid("BC1qwerty"))

    def test_pubkey_matches_address(self):
        w = make_wallet()
        self.assertEqual(crypto.pubkey_to_address(w["pubkey"]), w["address"])


class TestKeystore(unittest.TestCase):
    def test_roundtrip(self):
        _, secret = wallet_mod.generate_keypair()
        enc = wallet_mod.encrypt_secret(secret, "correct horse")
        self.assertEqual(wallet_mod.decrypt_secret(enc, "correct horse"), secret)

    def test_wrong_passphrase_rejected(self):
        _, secret = wallet_mod.generate_keypair()
        enc = wallet_mod.encrypt_secret(secret, "correct horse")
        with self.assertRaises(ValueError):
            wallet_mod.decrypt_secret(enc, "wrong horse")

    def test_unique_salts(self):
        _, secret = wallet_mod.generate_keypair()
        e1 = wallet_mod.encrypt_secret(secret, "p")
        e2 = wallet_mod.encrypt_secret(secret, "p")
        self.assertNotEqual(e1["salt_b64"], e2["salt_b64"])


class TestTransactionRules(unittest.TestCase):
    def test_amount_must_be_positive_integer(self):
        w = make_wallet()
        to = w["address"]
        with self.assertRaises(ValueError):
            tx_mod.build_transfer(to, to, 0, 1)
        with self.assertRaises(ValueError):
            tx_mod.build_transfer(to, to, 1.5, 1)
        with self.assertRaises(ValueError):
            tx_mod.build_transfer(to, to, -1, 1)

    def test_addresses_validated(self):
        w = make_wallet()
        with self.assertRaises(ValueError):
            tx_mod.build_transfer("not-an-address", w["address"], 1, 1)
        with self.assertRaises(ValueError):
            tx_mod.build_transfer(w["address"], "KLEX1zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", 1, 1)

    def test_memo_length_enforced(self):
        w = make_wallet()
        with self.assertRaises(ValueError):
            tx_mod.build_transfer(w["address"], w["address"], 1, 1, memo="x" * 97)
        ok = tx_mod.build_transfer(w["address"], w["address"], 1, 1, memo="x" * 96)
        self.assertEqual(len(ok["memo"]), 96)

    def test_signature_covers_all_fields(self):
        w = make_wallet()
        to = w["address"]
        tx = tx_mod.build_transfer(to, to, 3, 2, fee=1, memo="m")
        signed = tx_mod.sign_transfer(tx, w["pubkey"], w["secret"])
        self.assertTrue(wallet_mod.verify(w["pubkey"], tx_mod.signing_payload(tx), crypto.decode_b64(signed["sig_b64"])))
        tampered = dict(signed)
        tampered["amount"] = 4
        self.assertFalse(
            wallet_mod.verify(w["pubkey"], tx_mod.signing_payload(tampered), crypto.decode_b64(signed["sig_b64"]))
        )


if __name__ == "__main__":
    unittest.main()