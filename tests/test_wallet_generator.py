import unittest
import json
import os
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from wallet_generator import WalletGenerator


class TestWalletGenerator(unittest.TestCase):
    def setUp(self):
        # Use temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.generator = WalletGenerator(data_dir=os.path.join(self.temp_dir, "test_wallets"))
    
    def test_init(self):
        self.assertEqual(len(self.generator.wallets["wallets"]), 0)
        self.assertIn("metadata", self.generator.wallets)
    
    def test_generate_single_wallet(self):
        wallet = self.generator.generate_wallet("ethereum")
        self.assertIn("id", wallet)
        self.assertIn("chain", wallet)
        self.assertIn("address", wallet)
        self.assertIn("private_key", wallet)
        self.assertEqual(wallet["chain"], "ethereum")
        self.assertTrue(wallet["address"].startswith("0x"))
        self.assertEqual(len(wallet["private_key"]), 64)  # 32 bytes = 64 hex chars
    
    def test_generate_batch(self):
        count = 5
        wallets = self.generator.generate_batch(count, "ethereum")
        self.assertEqual(len(wallets), count)
        # Verify all have unique IDs
        ids = [w["id"] for w in wallets]
        self.assertEqual(len(set(ids)), count)
    
    def test_multi_chain_generation(self):
        result = self.generator.generate_multi_chain(2)
        self.assertIn("ethereum", result)
        self.assertIn("bitcoin_testnet", result)
        self.assertIn("solana_testnet", result)
        self.assertEqual(len(result["ethereum"]), 2)
        self.assertEqual(len(result["bitcoin_testnet"]), 2)
        self.assertEqual(len(result["solana_testnet"]), 2)
    
    def test_unsupported_chain(self):
        with self.assertRaises(ValueError):
            self.generator.generate_wallet("unsupported_chain")
    
    def test_get_wallet(self):
        wallet = self.generator.generate_wallet("ethereum")
        retrieved = self.generator.get_wallet(wallet["id"])
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], wallet["id"])
    
    def test_get_wallet_not_found(self):
        retrieved = self.generator.get_wallet("nonexistent")
        self.assertIsNone(retrieved)
    
    def test_get_addresses(self):
        self.generator.generate_batch(3, "ethereum")
        addresses = self.generator.get_addresses()
        self.assertEqual(len(addresses), 3)
        self.assertTrue(all(addr.startswith("0x") for addr in addresses))
    
    def test_get_addresses_filtered(self):
        self.generator.generate_batch(2, "ethereum")
        self.generator.generate_batch(2, "bitcoin_testnet")
        eth_addresses = self.generator.get_addresses(chain="ethereum")
        btc_addresses = self.generator.get_addresses(chain="bitcoin_testnet")
        self.assertEqual(len(eth_addresses), 2)
        self.assertEqual(len(btc_addresses), 2)
    
    def test_statistics(self):
        self.generator.generate_batch(3, "ethereum")
        self.generator.generate_batch(2, "bitcoin_testnet")
        stats = self.generator.get_statistics()
        self.assertEqual(stats["total_wallets"], 5)
        self.assertEqual(stats["chains"]["ethereum"], 3)
        self.assertEqual(stats["chains"]["bitcoin_testnet"], 2)
    
    def test_export_public_addresses(self):
        self.generator.generate_batch(2, "ethereum")
        filepath = self.generator.export_public_addresses()
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r") as f:
            data = json.load(f)
        self.assertEqual(data["total_addresses"], 2)
        # Verify no private keys in export
        for addr in data["addresses"]:
            self.assertNotIn("private_key", addr)
    
    def test_persistence(self):
        # Generate wallets
        self.generator.generate_batch(3, "ethereum")
        
        # Create new instance pointing to same directory
        new_generator = WalletGenerator(data_dir=self.generator.data_dir)
        self.assertEqual(len(new_generator.wallets["wallets"]), 3)
    
    def test_btc_address_format(self):
        wallet = self.generator.generate_wallet("bitcoin_testnet")
        self.assertTrue(wallet["address"].startswith("m") or wallet["address"].startswith("n"))
    
    def test_sol_address_format(self):
        wallet = self.generator.generate_wallet("solana_testnet")
        self.assertTrue(wallet["address"].startswith("So1"))


if __name__ == "__main__":
    unittest.main()
