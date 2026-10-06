"""
Unit Tests: Digital Data Generator
==================================
Verifies:
1. Pure random stream generation (length, binary validation, bit distribution).
2. Pattern-injected streams (8 consecutive zeros for B8ZS, 4 consecutive zeros for HDB3).
3. Deterministic repeatability via seed.
4. Input validation and error conditions.
"""

import unittest
from src.generator.data_generator import DataGenerator


class TestDataGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.gen = DataGenerator(seed=42)

    def test_generate_random_length_and_validity(self) -> None:
        """Verify length and character validity of random stream."""
        for length in [1, 10, 64, 128]:
            stream = self.gen.generate_random(length)
            self.assertEqual(len(stream), length)
            self.assertTrue(DataGenerator.validate_stream(stream))

    def test_generate_random_distribution(self) -> None:
        """Verify bit distribution is roughly balanced (p ~ 0.5) over large N."""
        stream = self.gen.generate_random(10000)
        zeros = stream.count("0")
        ones = stream.count("1")
        # Over 10,000 bits, ratio should be within 45% - 55%
        self.assertTrue(4500 <= zeros <= 5500)
        self.assertTrue(4500 <= ones <= 5500)

    def test_seed_determinism(self) -> None:
        """Verify identical seed produces identical bitstream."""
        gen1 = DataGenerator(seed=12345)
        gen2 = DataGenerator(seed=12345)
        stream1 = gen1.generate_random(50)
        stream2 = gen2.generate_random(50)
        self.assertEqual(stream1, stream2)

    def test_fixed_eight_zeros_injection(self) -> None:
        """Verify presence of 8 consecutive zeros for B8ZS scrambling."""
        stream = self.gen.generate_with_fixed_zeros(length=32, zero_run_length=8, num_injections=1)
        self.assertEqual(len(stream), 32)
        self.assertTrue(DataGenerator.validate_stream(stream))
        self.assertIn("00000000", stream)

    def test_fixed_four_zeros_injection(self) -> None:
        """Verify presence of 4 consecutive zeros for HDB3 scrambling."""
        stream = self.gen.generate_with_fixed_zeros(length=20, zero_run_length=4, num_injections=2)
        self.assertEqual(len(stream), 20)
        self.assertTrue(DataGenerator.validate_stream(stream))
        self.assertIn("0000", stream)

    def test_invalid_lengths(self) -> None:
        """Verify errors raised on invalid parameters."""
        with self.assertRaises(ValueError):
            self.gen.generate_random(0)
        with self.assertRaises(ValueError):
            self.gen.generate_random(-5)
        with self.assertRaises(ValueError):
            self.gen.generate_with_fixed_zeros(length=5, zero_run_length=8)  # 8 > 5


if __name__ == "__main__":
    unittest.main()
