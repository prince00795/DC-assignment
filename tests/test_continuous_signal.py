"""
Unit Tests: ContinuousSignal & ToneComponent
============================================
Verifies:
1. Sinusoidal signal evaluation (amplitude, frequency, phase, DC offset).
2. Nyquist sampling rate computation (f_nyquist = 2 * f_max).
3. Uniform sampling discretization and time grid.
4. Composite multi-tone harmonics.
"""

import math
import unittest
from src.analog.continuous_signal import ContinuousSignal, ToneComponent


class TestContinuousSignal(unittest.TestCase):
    def test_single_sine_evaluation(self) -> None:
        # A = 2.0, f = 1.0 Hz, phi = 0
        sig = ContinuousSignal.create_simple_sine(amplitude=2.0, frequency=1.0)
        # At t = 0: sin(0) = 0
        self.assertAlmostEqual(sig.evaluate(0.0), 0.0, places=5)
        # At t = 0.25 (quarter cycle): sin(pi/2) = 1.0 -> 2.0
        self.assertAlmostEqual(sig.evaluate(0.25), 2.0, places=5)
        # At t = 0.5 (half cycle): sin(pi) = 0
        self.assertAlmostEqual(sig.evaluate(0.5), 0.0, places=5)
        # At t = 0.75 (three-quarter cycle): sin(3pi/2) = -1.0 -> -2.0
        self.assertAlmostEqual(sig.evaluate(0.75), -2.0, places=5)

    def test_dc_offset(self) -> None:
        sig = ContinuousSignal.create_simple_sine(amplitude=1.0, frequency=2.0, dc_offset=3.0)
        self.assertAlmostEqual(sig.evaluate(0.0), 3.0, places=5)
        self.assertAlmostEqual(sig.evaluate(0.125), 4.0, places=5)

    def test_nyquist_rate_calculation(self) -> None:
        # Tone 1: 5 Hz, Tone 2: 15 Hz -> f_max = 15 Hz, Nyquist = 30 Hz
        sig = ContinuousSignal(
            tones=[
                ToneComponent(amplitude=1.0, frequency=5.0),
                ToneComponent(amplitude=0.5, frequency=15.0),
            ]
        )
        self.assertEqual(sig.max_frequency, 15.0)
        self.assertEqual(sig.nyquist_rate, 30.0)
        self.assertTrue(sig.is_nyquist_satisfied(30.0))
        self.assertTrue(sig.is_nyquist_satisfied(40.0))
        self.assertFalse(sig.is_nyquist_satisfied(25.0))

    def test_uniform_sampling(self) -> None:
        sig = ContinuousSignal.create_simple_sine(amplitude=1.0, frequency=2.0)
        fs = 100.0  # 100 Hz
        duration = 0.5  # 0.5 s -> 50 samples
        times, values = sig.sample(sampling_rate=fs, duration=duration)
        self.assertEqual(len(times), 50)
        self.assertEqual(len(values), 50)
        self.assertAlmostEqual(times[0], 0.0)
        self.assertAlmostEqual(times[1], 0.01)
        self.assertAlmostEqual(values[0], 0.0)


if __name__ == "__main__":
    unittest.main()
