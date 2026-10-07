"""
Unit Tests: Digital Data Generator
==================================
Verifies:
1. Pure random stream generation (length, binary validation, bit distribution).
2. Pattern-injected streams (8 consecutive zeros for B8ZS, 4 consecutive zeros for HDB3).
3. Specialized B8ZS and HDB3 convenience generators.
4. Custom pattern injection (exact position, random position, overwrite, insert).
5. Zero-run detection and maximum consecutive zero analysis.
6. Deterministic repeatability via seed.
7. Input validation and boundary error conditions.
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

    def test_generate_b8zs_stream(self) -> None:
        """Verify dedicated B8ZS generator ensures 8 consecutive zeros."""
        stream = self.gen.generate_b8zs_stream(length=40, num_injections=2)
        self.assertEqual(len(stream), 40)
        self.assertTrue(DataGenerator.validate_stream(stream))
        self.assertIn("00000000", stream)
        self.assertGreaterEqual(DataGenerator.max_consecutive_zeros(stream), 8)

    def test_generate_hdb3_stream(self) -> None:
        """Verify dedicated HDB3 generator ensures 4 consecutive zeros."""
        stream = self.gen.generate_hdb3_stream(length=25, num_injections=3)
        self.assertEqual(len(stream), 25)
        self.assertTrue(DataGenerator.validate_stream(stream))
        self.assertIn("0000", stream)
        self.assertGreaterEqual(DataGenerator.max_consecutive_zeros(stream), 4)

    def test_inject_pattern_overwrite(self) -> None:
        """Verify custom pattern injection with overwrite mode at specific position."""
        base = "1111111111"
        pattern = "0000"
        result = self.gen.inject_pattern(base, pattern, position=2, overwrite=True)
        self.assertEqual(result, "1100001111")
        self.assertEqual(len(result), len(base))

    def test_inject_pattern_insert(self) -> None:
        """Verify custom pattern injection with insert mode at specific position."""
        base = "1111"
        pattern = "00000000"
        result = self.gen.inject_pattern(base, pattern, position=2, overwrite=False)
        self.assertEqual(result, "110000000011")
        self.assertEqual(len(result), len(base) + len(pattern))

    def test_find_zero_runs_and_max(self) -> None:
        """Verify detection of zero runs and max consecutive zeros."""
        stream = "101100011000000001"
        runs = DataGenerator.find_zero_runs(stream)
        # Expected zero runs at: index 1 (len 1), index 4 (len 3), index 9 (len 8)
        self.assertEqual(runs, [(1, 1), (4, 3), (9, 8)])
        self.assertEqual(DataGenerator.max_consecutive_zeros(stream), 8)

        # All ones
        self.assertEqual(DataGenerator.find_zero_runs("1111"), [])
        self.assertEqual(DataGenerator.max_consecutive_zeros("1111"), 0)

        # All zeros
        self.assertEqual(DataGenerator.find_zero_runs("00000"), [(0, 5)])
        self.assertEqual(DataGenerator.max_consecutive_zeros("00000"), 5)

    def test_invalid_lengths_and_patterns(self) -> None:
        """Verify errors raised on invalid parameters."""
        with self.assertRaises(ValueError):
            self.gen.generate_random(0)
        with self.assertRaises(ValueError):
            self.gen.generate_random(-5)
        with self.assertRaises(ValueError):
            self.gen.generate_with_fixed_zeros(length=5, zero_run_length=8)
        with self.assertRaises(ValueError):
            self.gen.inject_pattern("111", "0000", overwrite=True)  # pattern longer than base
        with self.assertRaises(IndexError):
            self.gen.inject_pattern("1111", "00", position=10, overwrite=True)
        with self.assertRaises(ValueError):
            self.gen.inject_pattern("1111", "abc")  # non-binary pattern


if __name__ == "__main__":
    unittest.main()
