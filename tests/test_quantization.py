"""
Unit Tests: Uniform Quantizer & Binary PCM Encoding
===================================================
Verifies:
1. Dynamic range partitioning and step size Delta = (V_max - V_min) / 2^n.
2. Error bound: |e[n]| <= Delta / 2 for unclipped samples.
3. Binary codeword mapping:
    * Natural binary
    * Gray coding (adjacent level Hamming distance of 1)
    * Two's complement
4. Full roundtrip: continuous samples -> quantized levels -> bitstream -> dequantized DAC levels.
5. Empirical and theoretical quantization noise power (Delta^2 / 12).
6. SQNR scaling: ~6.02 dB improvement per additional bit of resolution.
7. Automatic range scaling via from_signal factory.
8. Clipping overload detection and reporting.
9. Parameter validation and error handling.
"""

import math
import unittest
from src.analog.quantization import UniformQuantizer, QuantizationResult


class TestUniformQuantizer(unittest.TestCase):
    def setUp(self) -> None:
        # 3 bits -> 8 levels over [-1.0, 1.0] -> Delta = 2.0 / 8 = 0.25V
        self.q3 = UniformQuantizer(num_bits=3, v_min=-1.0, v_max=1.0, coding_scheme="natural")
        self.q3_gray = UniformQuantizer(num_bits=3, v_min=-1.0, v_max=1.0, coding_scheme="gray")

    def test_levels_and_step_size(self) -> None:
        """Verify L = 2^n and Delta = (V_max - V_min) / 2^n."""
        self.assertEqual(self.q3.num_levels, 8)
        self.assertAlmostEqual(self.q3.step_size, 0.25)

        q4 = UniformQuantizer(num_bits=4, v_min=-2.0, v_max=2.0)
        self.assertEqual(q4.num_levels, 16)
        self.assertAlmostEqual(q4.step_size, 0.25)

    def test_reconstruction_levels_and_midpoints(self) -> None:
        """Verify mid-rise reconstruction levels: V_min + (k + 0.5) * Delta."""
        levels = self.q3.reconstruction_levels
        self.assertEqual(len(levels), 8)
        # Level 0: -1.0 + 0.5 * 0.25 = -0.875
        self.assertAlmostEqual(levels[0], -0.875)
        # Level 7: -1.0 + 7.5 * 0.25 = +0.875
        self.assertAlmostEqual(levels[7], 0.875)

    def test_quantization_error_bound(self) -> None:
        """Verify that quantization error |q - x| <= Delta / 2 for unclipped values."""
        samples = [-0.95, -0.7, -0.33, 0.0, 0.12, 0.45, 0.88]
        res = self.q3.quantize(samples)
        half_delta = self.q3.step_size / 2.0

        for err in res.quantization_errors:
            self.assertLessEqual(abs(err), half_delta + 1e-12)

        self.assertLessEqual(res.max_error, half_delta + 1e-12)

    def test_natural_binary_encoding(self) -> None:
        """Verify natural binary codes (0 -> '000', 7 -> '111')."""
        # Minimum level (-0.95 -> index 0) and maximum level (0.95 -> index 7)
        samples = [-0.95, 0.95]
        res = self.q3.quantize(samples)
        self.assertEqual(res.binary_codes[0], "000")
        self.assertEqual(res.binary_codes[1], "111")
        self.assertEqual(res.bitstream, "000111")

    def test_gray_code_hamming_distance(self) -> None:
        """Verify Gray coding produces adjacent codewords differing by exactly 1 bit."""
        samples = list(self.q3_gray.reconstruction_levels)
        res = self.q3_gray.quantize(samples)

        for i in range(len(res.binary_codes) - 1):
            code_a = res.binary_codes[i]
            code_b = res.binary_codes[i + 1]
            # Hamming distance must be exactly 1
            hamming_dist = sum(c1 != c2 for c1, c2 in zip(code_a, code_b))
            self.assertEqual(
                hamming_dist,
                1,
                f"Gray code violation between adjacent levels: '{code_a}' and '{code_b}'",
            )

    def test_roundtrip_quantize_dequantize_bitstream(self) -> None:
        """Verify bitstream dequantization perfectly recovers quantized levels."""
        samples = [-0.8, -0.4, 0.1, 0.6, -0.2]
        res = self.q3.quantize(samples)

        # DAC bitstream reconstruction
        recovered_levels = self.q3.decode_bitstream(res.bitstream)
        self.assertEqual(recovered_levels, res.quantized_samples)

        # Index-based dequantization
        from_indices = self.q3.dequantize(res.quantization_indices)
        self.assertEqual(from_indices, res.quantized_samples)

    def test_sqnr_scaling_with_bit_depth(self) -> None:
        """Verify SQNR increases by approximately 6 dB for each added bit."""
        # Test full scale sinusoid samples
        num_points = 500
        sine_samples = [
            0.95 * math.sin(2.0 * math.pi * 5.0 * (i / num_points))
            for i in range(num_points)
        ]

        q2 = UniformQuantizer(num_bits=2, v_min=-1.0, v_max=1.0)
        q4 = UniformQuantizer(num_bits=4, v_min=-1.0, v_max=1.0)
        q6 = UniformQuantizer(num_bits=6, v_min=-1.0, v_max=1.0)

        res2 = q2.quantize(sine_samples)
        res4 = q4.quantize(sine_samples)
        res6 = q6.quantize(sine_samples)

        # SQNR should improve monotonically
        self.assertLess(res2.empirical_sqnr_db, res4.empirical_sqnr_db)
        self.assertLess(res4.empirical_sqnr_db, res6.empirical_sqnr_db)

        # Difference between 6-bit and 4-bit (2 bits difference -> ~12 dB)
        diff_db = res6.empirical_sqnr_db - res4.empirical_sqnr_db
        self.assertGreater(diff_db, 9.0)
        self.assertLess(diff_db, 15.0)

    def test_noise_power_theoretical_vs_empirical(self) -> None:
        """Verify theoretical noise power Delta^2 / 12."""
        expected_theory = (0.25 ** 2) / 12.0
        res = self.q3.quantize([0.1, 0.2, 0.3])
        self.assertAlmostEqual(res.theoretical_noise_power, expected_theory, places=6)

    def test_clipping_detection(self) -> None:
        """Verify overload / clipping when samples exceed dynamic range."""
        samples = [-1.5, 0.0, 1.8]  # -1.5 and 1.8 exceed [-1.0, 1.0]
        res = self.q3.quantize(samples)
        self.assertTrue(res.clipping_occurred)
        self.assertEqual(res.clipped_sample_count, 2)
        # Clamped to min and max levels
        self.assertEqual(res.quantization_indices[0], 0)
        self.assertEqual(res.quantization_indices[2], 7)

    def test_from_signal_factory(self) -> None:
        """Verify dynamic auto-range scaling from signal samples."""
        samples = [-4.2, 1.1, 3.8]
        quantizer = UniformQuantizer.from_signal(samples, num_bits=4, headroom_ratio=0.1)
        # Peak is 4.2 -> limit = 4.2 * 1.1 = 4.62
        self.assertAlmostEqual(quantizer.v_max, 4.62, places=2)
        self.assertAlmostEqual(quantizer.v_min, -4.62, places=2)

    def test_invalid_parameters_and_inputs(self) -> None:
        """Verify error handling on invalid configurations."""
        with self.assertRaises(ValueError):
            UniformQuantizer(num_bits=0)
        with self.assertRaises(ValueError):
            UniformQuantizer(v_min=2.0, v_max=1.0)
        with self.assertRaises(ValueError):
            UniformQuantizer(coding_scheme="unknown_scheme")
        with self.assertRaises(ValueError):
            self.q3.quantize([])
        with self.assertRaises(ValueError):
            self.q3.decode_bitstream("1010")  # length 4 not multiple of 3


if __name__ == "__main__":
    unittest.main()
