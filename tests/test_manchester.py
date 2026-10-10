"""
Unit Tests: Manchester Line Encoder & Edge Detector Decoder
============================================================
Verifies:
1. IEEE 802.3 Convention (0 -> High-to-Low, 1 -> Low-to-High).
2. G.E. Thomas Convention (0 -> Low-to-High, 1 -> High-to-Low).
3. Guaranteed mid-bit transitions on every bit interval (self-clocking).
4. Bit boundary transitions on consecutive identical bits.
5. Zero DC bias property across all bitstreams.
6. Full round-trip encode-to-decode bitstream reconstruction.
7. Signal violation detection on flat / un-transitioned waveform slices.
8. Parameter validation and error handling.
"""

import unittest
from src.line_coding.encoders import ManchesterEncoder


class TestManchesterEncoder(unittest.TestCase):
    def setUp(self) -> None:
        self.encoder_ieee = ManchesterEncoder(
            samples_per_bit=40,
            bit_duration=1.0,
            positive_voltage=2.0,
            negative_voltage=-2.0,
            convention="ieee",
        )
        self.encoder_thomas = ManchesterEncoder(
            samples_per_bit=40,
            bit_duration=1.0,
            positive_voltage=2.0,
            negative_voltage=-2.0,
            convention="thomas",
        )

    def test_ieee_voltage_mapping(self) -> None:
        """Verify IEEE 802.3 convention: 0 is High-to-Low, 1 is Low-to-High."""
        v0_first, v0_second = self.encoder_ieee.bit_to_half_voltages("0")
        self.assertEqual(v0_first, 2.0)
        self.assertEqual(v0_second, -2.0)

        v1_first, v1_second = self.encoder_ieee.bit_to_half_voltages("1")
        self.assertEqual(v1_first, -2.0)
        self.assertEqual(v1_second, 2.0)

    def test_thomas_voltage_mapping(self) -> None:
        """Verify G.E. Thomas convention: 0 is Low-to-High, 1 is High-to-Low."""
        v0_first, v0_second = self.encoder_thomas.bit_to_half_voltages("0")
        self.assertEqual(v0_first, -2.0)
        self.assertEqual(v0_second, 2.0)

        v1_first, v1_second = self.encoder_thomas.bit_to_half_voltages("1")
        self.assertEqual(v1_first, 2.0)
        self.assertEqual(v1_second, -2.0)

    def test_waveform_structure_and_levels(self) -> None:
        """Verify discrete time array and split voltage levels."""
        bits = "01"
        wf = self.encoder_ieee.encode(bits)
        self.assertEqual(wf.num_bits, 2)
        self.assertEqual(wf.total_samples, 80)
        self.assertEqual(wf.total_duration, 2.0)

        # Bit 0 ('0'): first 20 samples +2.0V, next 20 samples -2.0V
        _, v_bit0 = wf.get_bit_slice(0)
        self.assertTrue(all(v == 2.0 for v in v_bit0[:20]))
        self.assertTrue(all(v == -2.0 for v in v_bit0[20:]))

        # Bit 1 ('1'): first 20 samples -2.0V, next 20 samples +2.0V
        _, v_bit1 = wf.get_bit_slice(1)
        self.assertTrue(all(v == -2.0 for v in v_bit1[:20]))
        self.assertTrue(all(v == 2.0 for v in v_bit1[20:]))

    def test_guaranteed_transitions_and_boundary_transitions(self) -> None:
        """Verify mid-bit and boundary transitions."""
        # For '00' in IEEE:
        # Bit 0: +2 then -2
        # Bit 1: +2 then -2
        # Boundary transition from -2 to +2 between bit 0 and bit 1!
        # Total transitions: 2 midbit + 1 boundary = 3 transitions
        wf_00 = self.encoder_ieee.encode("00")
        self.assertEqual(wf_00.metadata["midbit_transitions"], 2)
        self.assertEqual(wf_00.metadata["boundary_transitions"], 1)
        self.assertEqual(wf_00.metadata["transitions"], 3)
        self.assertEqual(wf_00.metadata["transition_density"], 1.5)

        # For '01' in IEEE:
        # Bit 0: +2 then -2
        # Bit 1: -2 then +2
        # No boundary transition between -2 and -2!
        # Total transitions: 2 midbit + 0 boundary = 2 transitions
        wf_01 = self.encoder_ieee.encode("01")
        self.assertEqual(wf_01.metadata["boundary_transitions"], 0)
        self.assertEqual(wf_01.metadata["transitions"], 2)
        self.assertEqual(wf_01.metadata["transition_density"], 1.0)

    def test_zero_dc_bias_guarantee(self) -> None:
        """Verify net DC component is zero for all data sequences."""
        test_streams = ["0", "1", "00000000", "11111111", "101100101011"]
        for bits in test_streams:
            wf = self.encoder_ieee.encode(bits)
            self.assertAlmostEqual(wf.metadata["average_voltage"], 0.0, places=5)
            self.assertFalse(wf.metadata["has_dc_bias"])
            self.assertEqual(self.encoder_ieee.calculate_dc_bias(bits), 0.0)

    def test_roundtrip_encode_decode(self) -> None:
        """Verify receiver edge-detection decoding perfectly recovers bitstreams."""
        test_cases = [
            "0",
            "1",
            "0000",
            "1111",
            "10101010",
            "01010101",
            "11001010011100",
            "00000000",
            "10111010111000000001011011111100",
        ]
        for bits in test_cases:
            # IEEE convention roundtrip
            wf_ieee = self.encoder_ieee.encode(bits)
            decoded_ieee = self.encoder_ieee.decode(wf_ieee)
            self.assertEqual(decoded_ieee, bits, f"IEEE decode failed for '{bits}'")

            # Thomas convention roundtrip
            wf_thomas = self.encoder_thomas.encode(bits)
            decoded_thomas = self.encoder_thomas.decode(wf_thomas)
            self.assertEqual(decoded_thomas, bits, f"Thomas decode failed for '{bits}'")

    def test_violation_detection(self) -> None:
        """Verify decoder raises error on physical signal violation (no mid-bit transition)."""
        wf = self.encoder_ieee.encode("0")
        # Corrupt second half of bit 0 to be +2.0V (flat line)
        for i in range(len(wf.voltages)):
            wf.voltages[i] = 2.0
        with self.assertRaises(ValueError):
            self.encoder_ieee.decode(wf)

    def test_invalid_parameters_and_inputs(self) -> None:
        """Verify error handling on malformed configurations."""
        with self.assertRaises(ValueError):
            ManchesterEncoder(convention="invalid_convention")
        with self.assertRaises(ValueError):
            ManchesterEncoder(samples_per_bit=2)  # must be >= 4
        with self.assertRaises(ValueError):
            self.encoder_ieee.encode("")
        with self.assertRaises(ValueError):
            self.encoder_ieee.encode("10201")


if __name__ == "__main__":
    unittest.main()
