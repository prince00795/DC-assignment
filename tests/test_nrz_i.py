"""
Unit Tests: NRZ-I Line Encoder & Differential Decoder
=====================================================
Verifies:
1. Differential transition rule (bit '1' triggers inversion, bit '0' maintains level in standard mode).
2. Inverted transition rule (bit '0' triggers inversion, bit '1' maintains level).
3. Initial reference voltage configuration (+V vs -V).
4. SignalWaveform generation (time grid, continuous bit intervals).
5. Midpoint receiver probing.
6. Full round-trip encode-to-decode bitstream reconstruction.
7. Differential transition tracking (indices, counts, density).
8. DC bias computation under various bit sequences.
9. Parameter validation and error handling.
"""

import unittest
from src.line_coding.encoders import NRZIEncoder


class TestNRZIEncoder(unittest.TestCase):
    def setUp(self) -> None:
        self.encoder_std = NRZIEncoder(
            samples_per_bit=50,
            bit_duration=1.0,
            positive_voltage=2.0,
            negative_voltage=-2.0,
            transition_on_one=True,
            initial_voltage=2.0,  # starts at +2.0V
        )
        self.encoder_inv = NRZIEncoder(
            samples_per_bit=50,
            bit_duration=1.0,
            positive_voltage=2.0,
            negative_voltage=-2.0,
            transition_on_one=False,
            initial_voltage=2.0,
        )

    def test_transition_on_one_logic(self) -> None:
        """Verify that '1' triggers a level transition and '0' holds level."""
        # Initial level is +2.0V
        # Bit 0: '1' -> inverts from +2.0V to -2.0V
        # Bit 1: '0' -> holds at -2.0V
        # Bit 2: '1' -> inverts from -2.0V to +2.0V
        # Bit 3: '0' -> holds at +2.0V
        bits = "1010"
        wf = self.encoder_std.encode(bits)
        levels = wf.metadata["bit_levels"]
        self.assertEqual(levels, [-2.0, -2.0, 2.0, 2.0])
        self.assertEqual(wf.metadata["transitions"], 2)
        self.assertEqual(wf.metadata["transition_indices"], [0, 2])

    def test_transition_on_zero_logic(self) -> None:
        """Verify inverted mode where '0' triggers a transition and '1' holds."""
        # Initial level is +2.0V
        # Bit 0: '0' -> inverts from +2.0V to -2.0V
        # Bit 1: '1' -> holds at -2.0V
        # Bit 2: '0' -> inverts from -2.0V to +2.0V
        # Bit 3: '1' -> holds at +2.0V
        bits = "0101"
        wf = self.encoder_inv.encode(bits)
        levels = wf.metadata["bit_levels"]
        self.assertEqual(levels, [-2.0, -2.0, 2.0, 2.0])
        self.assertEqual(wf.metadata["transitions"], 2)
        self.assertEqual(wf.metadata["transition_indices"], [0, 2])

    def test_initial_voltage_variations(self) -> None:
        """Verify encoder behavior when initial voltage starts at negative level."""
        # Initial level is -2.0V
        # Bit 0: '1' -> inverts to +2.0V
        # Bit 1: '1' -> inverts to -2.0V
        wf = self.encoder_std.encode("11", initial_voltage=-2.0)
        self.assertEqual(wf.metadata["bit_levels"], [2.0, -2.0])

        # Starts at +2.0V
        # Bit 0: '0' -> holds +2.0V
        # Bit 1: '0' -> holds +2.0V
        wf_zeros = self.encoder_std.encode("00", initial_voltage=2.0)
        self.assertEqual(wf_zeros.metadata["bit_levels"], [2.0, 2.0])
        self.assertEqual(wf_zeros.metadata["transitions"], 0)

    def test_waveform_structure_and_levels(self) -> None:
        """Verify SignalWaveform properties."""
        bits = "100"
        wf = self.encoder_std.encode(bits)
        self.assertEqual(wf.num_bits, 3)
        self.assertEqual(wf.total_samples, 150)
        self.assertEqual(wf.total_duration, 3.0)

        # Bit 0: '1' -> inverts to -2.0V across all samples
        _, v0 = wf.get_bit_slice(0)
        self.assertTrue(all(v == -2.0 for v in v0))

        # Bit 1: '0' -> stays at -2.0V
        _, v1 = wf.get_bit_slice(1)
        self.assertTrue(all(v == -2.0 for v in v1))

        # Bit 2: '0' -> stays at -2.0V
        _, v2 = wf.get_bit_slice(2)
        self.assertTrue(all(v == -2.0 for v in v2))

    def test_midpoint_sampling(self) -> None:
        """Verify midpoint probing returns proper bit interval levels."""
        bits = "110"
        wf = self.encoder_std.encode(bits)

        t0, v0 = wf.get_midpoint_sample(0)
        self.assertAlmostEqual(t0, 0.5, places=2)
        self.assertEqual(v0, -2.0)

        t1, v1 = wf.get_midpoint_sample(1)
        self.assertAlmostEqual(t1, 1.5, places=2)
        self.assertEqual(v1, 2.0)

        t2, v2 = wf.get_midpoint_sample(2)
        self.assertAlmostEqual(t2, 2.5, places=2)
        self.assertEqual(v2, 2.0)

    def test_roundtrip_encode_decode(self) -> None:
        """Verify physical signal differential decoding recovers bits with 100% fidelity."""
        test_cases = [
            "0",
            "1",
            "00000000",
            "11111111",
            "10101010",
            "01010101",
            "11001010011100",
            "00001000000001",
        ]
        for bits in test_cases:
            # Test standard convention
            wf_std = self.encoder_std.encode(bits)
            decoded_std = self.encoder_std.decode(wf_std)
            self.assertEqual(decoded_std, bits, f"Failed standard decode for '{bits}'")

            # Test inverted convention
            wf_inv = self.encoder_inv.encode(bits)
            decoded_inv = self.encoder_inv.decode(wf_inv)
            self.assertEqual(decoded_inv, bits, f"Failed inverted decode for '{bits}'")

    def test_transition_density(self) -> None:
        """Verify transition density calculations in NRZ-I."""
        # In NRZ-I with transition_on_one=True:
        # "1111": 4 transitions in 4 bits -> density 1.0
        self.assertEqual(self.encoder_std.calculate_transition_density("1111"), 1.0)

        # "0000": 0 transitions in 4 bits -> density 0.0
        self.assertEqual(self.encoder_std.calculate_transition_density("0000"), 0.0)

        # "1000": 1 transition in 4 bits -> density 0.25
        self.assertEqual(self.encoder_std.calculate_transition_density("1000"), 0.25)

        wf = self.encoder_std.encode("1000")
        self.assertEqual(wf.metadata["transition_density"], 0.25)

    def test_dc_bias_calculation(self) -> None:
        """Verify DC voltage component computation."""
        # Initial level +2.0V, bits = "11":
        # bit 0: -2.0V, bit 1: +2.0V -> average 0.0V
        bias_balanced = self.encoder_std.calculate_dc_bias("11", initial_voltage=2.0)
        self.assertAlmostEqual(bias_balanced, 0.0)

        # Initial level +2.0V, bits = "00":
        # bit 0: +2.0V, bit 1: +2.0V -> average 2.0V
        bias_high = self.encoder_std.calculate_dc_bias("00", initial_voltage=2.0)
        self.assertAlmostEqual(bias_high, 2.0)

    def test_invalid_parameters_and_inputs(self) -> None:
        """Verify error handling for invalid voltages and inputs."""
        with self.assertRaises(ValueError):
            NRZIEncoder(positive_voltage=1.0, negative_voltage=1.0)

        with self.assertRaises(ValueError):
            NRZIEncoder(positive_voltage=-2.0, negative_voltage=2.0)

        with self.assertRaises(ValueError):
            self.encoder_std.encode("")

        with self.assertRaises(ValueError):
            self.encoder_std.encode("10201")


if __name__ == "__main__":
    unittest.main()
