"""
Unit Tests: NRZ-L Line Encoder & Decoder
========================================
Verifies:
1. Voltage mapping conventions (standard telecom 0 -> +V, 1 -> -V and inverted 0 -> -V, 1 -> +V).
2. SignalWaveform generation (time grid, constant voltage levels per bit).
3. Mid-point receiver probing.
4. Full round-trip encode-to-decode bitstream reconstruction.
5. Signal analysis metrics (transitions, transition density, DC bias).
6. Parameter validation and error handling.
"""

import unittest
from src.line_coding.encoders import NRZLEncoder


class TestNRZLEncoder(unittest.TestCase):
    def setUp(self) -> None:
        self.encoder_std = NRZLEncoder(
            samples_per_bit=50,
            bit_duration=1.0,
            positive_voltage=2.0,
            negative_voltage=-2.0,
            zero_is_positive=True,
        )
        self.encoder_inv = NRZLEncoder(
            samples_per_bit=50,
            bit_duration=1.0,
            positive_voltage=2.0,
            negative_voltage=-2.0,
            zero_is_positive=False,
        )

    def test_bit_to_voltage_standard_mapping(self) -> None:
        """Verify standard telecom mapping: 0 -> +V, 1 -> -V."""
        self.assertEqual(self.encoder_std.bit_to_voltage("0"), 2.0)
        self.assertEqual(self.encoder_std.bit_to_voltage("1"), -2.0)

    def test_bit_to_voltage_inverted_mapping(self) -> None:
        """Verify inverted mapping: 0 -> -V, 1 -> +V."""
        self.assertEqual(self.encoder_inv.bit_to_voltage("0"), -2.0)
        self.assertEqual(self.encoder_inv.bit_to_voltage("1"), 2.0)

    def test_waveform_structure_and_levels(self) -> None:
        """Verify discrete time array and flat voltage levels across bit duration."""
        bits = "010"
        waveform = self.encoder_std.encode(bits)
        self.assertEqual(waveform.num_bits, 3)
        self.assertEqual(waveform.total_samples, 150)
        self.assertEqual(waveform.total_duration, 3.0)

        # Bit 0 ('0'): all samples should be +2.0V
        _, v_bit0 = waveform.get_bit_slice(0)
        self.assertTrue(all(v == 2.0 for v in v_bit0))

        # Bit 1 ('1'): all samples should be -2.0V
        _, v_bit1 = waveform.get_bit_slice(1)
        self.assertTrue(all(v == -2.0 for v in v_bit1))

        # Bit 2 ('0'): all samples should be +2.0V
        _, v_bit2 = waveform.get_bit_slice(2)
        self.assertTrue(all(v == 2.0 for v in v_bit2))

    def test_midpoint_sampling(self) -> None:
        """Verify mid-point probe values at (i + 0.5) * Tb."""
        bits = "101"
        waveform = self.encoder_std.encode(bits)

        t0, v0 = waveform.get_midpoint_sample(0)
        self.assertAlmostEqual(t0, 0.5, places=2)
        self.assertEqual(v0, -2.0)  # bit '1' -> -2.0V

        t1, v1 = waveform.get_midpoint_sample(1)
        self.assertAlmostEqual(t1, 1.5, places=2)
        self.assertEqual(v1, 2.0)   # bit '0' -> +2.0V

    def test_roundtrip_encode_decode(self) -> None:
        """Verify physical signal decoding flawlessly recovers original bits."""
        test_cases = [
            "0",
            "1",
            "01010101",
            "00001111",
            "11001010011100",
            "00000000",
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

    def test_transitions_and_transition_density(self) -> None:
        """Verify transition count and density."""
        # "0101" has 3 transitions out of 3 possible -> density = 1.0
        self.assertEqual(self.encoder_std.calculate_transition_density("0101"), 1.0)

        # "0000" has 0 transitions -> density = 0.0
        self.assertEqual(self.encoder_std.calculate_transition_density("0000"), 0.0)

        # "0011" has 1 transition out of 3 possible -> density = 1/3
        self.assertAlmostEqual(self.encoder_std.calculate_transition_density("0011"), 1.0 / 3.0)

        # Check metadata
        wf = self.encoder_std.encode("0101")
        self.assertEqual(wf.metadata["transitions"], 3)
        self.assertEqual(wf.metadata["transition_density"], 1.0)

    def test_dc_bias_calculation(self) -> None:
        """Verify average DC voltage calculation."""
        # Balanced "01": average of +2.0 and -2.0 is 0.0
        self.assertAlmostEqual(self.encoder_std.calculate_dc_bias("01"), 0.0)
        wf_balanced = self.encoder_std.encode("01")
        self.assertFalse(wf_balanced.metadata["has_dc_bias"])

        # Unbalanced "0001": average is (3*2.0 - 2.0) / 4 = 1.0V
        self.assertAlmostEqual(self.encoder_std.calculate_dc_bias("0001"), 1.0)
        wf_unbalanced = self.encoder_std.encode("0001")
        self.assertTrue(wf_unbalanced.metadata["has_dc_bias"])
        self.assertAlmostEqual(wf_unbalanced.metadata["average_voltage"], 1.0)

    def test_invalid_parameters_and_inputs(self) -> None:
        """Verify error handling on invalid voltage bounds and malformed inputs."""
        with self.assertRaises(ValueError):
            NRZLEncoder(positive_voltage=1.0, negative_voltage=1.0)  # pos must be > neg
        with self.assertRaises(ValueError):
            NRZLEncoder(positive_voltage=-1.0, negative_voltage=1.0)

        with self.assertRaises(ValueError):
            self.encoder_std.encode("")
        with self.assertRaises(ValueError):
            self.encoder_std.encode("01021")
        with self.assertRaises(ValueError):
            self.encoder_std.bit_to_voltage("2")


if __name__ == "__main__":
    unittest.main()
