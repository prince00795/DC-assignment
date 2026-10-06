"""
Unit Tests: Line Coding Base & SignalWaveform
=============================================
Verifies:
1. SignalWaveform data model (time arrays, voltage levels, lengths).
2. Bit slice extraction and midpoint sample calculations.
3. Base encoder input validation and parameter checking.
"""

import unittest
from src.line_coding.base import SignalWaveform, LineEncoder


class DummyEncoder(LineEncoder):
    """Concrete test implementation of LineEncoder."""
    @property
    def scheme_name(self) -> str:
        return "Dummy"

    def encode(self, bits: str) -> SignalWaveform:
        self._validate_input(bits)
        t_points = []
        voltages = []
        dt = self.bit_duration / self.samples_per_bit
        for bit_idx, bit in enumerate(bits):
            level = self.positive_voltage if bit == "1" else self.negative_voltage
            for s in range(self.samples_per_bit):
                t_points.append((bit_idx * self.samples_per_bit + s) * dt)
                voltages.append(level)
        return SignalWaveform(
            bits=bits,
            time_points=t_points,
            voltages=voltages,
            samples_per_bit=self.samples_per_bit,
            bit_duration=self.bit_duration,
        )


class TestLineCodingBase(unittest.TestCase):
    def setUp(self) -> None:
        self.encoder = DummyEncoder(samples_per_bit=10, bit_duration=1.0)

    def test_signal_waveform_properties(self) -> None:
        waveform = self.encoder.encode("1010")
        self.assertEqual(waveform.num_bits, 4)
        self.assertEqual(waveform.total_duration, 4.0)
        self.assertEqual(waveform.total_samples, 40)
        self.assertEqual(len(waveform.time_points), 40)
        self.assertEqual(len(waveform.voltages), 40)

    def test_bit_slice_extraction(self) -> None:
        waveform = self.encoder.encode("10")
        t_slice, v_slice = waveform.get_bit_slice(0)
        self.assertEqual(len(t_slice), 10)
        self.assertEqual(len(v_slice), 10)
        # In DummyEncoder, bit '1' is positive voltage (1.0)
        self.assertTrue(all(v == 1.0 for v in v_slice))

        t_slice1, v_slice1 = waveform.get_bit_slice(1)
        # Bit '0' is negative voltage (-1.0)
        self.assertTrue(all(v == -1.0 for v in v_slice1))

    def test_midpoint_sample(self) -> None:
        waveform = self.encoder.encode("10")
        t_mid, v_mid = waveform.get_midpoint_sample(0)
        # Midpoint of bit 0 with bit_duration 1.0 is 0.5s
        self.assertAlmostEqual(t_mid, 0.5, places=2)
        self.assertEqual(v_mid, 1.0)

    def test_invalid_input_validation(self) -> None:
        with self.assertRaises(ValueError):
            self.encoder.encode("")
        with self.assertRaises(ValueError):
            self.encoder.encode("1021")  # '2' is invalid
        with self.assertRaises(ValueError):
            self.encoder.encode("abc")


if __name__ == "__main__":
    unittest.main()
