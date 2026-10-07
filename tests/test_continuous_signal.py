"""
Unit Tests: ContinuousSignal, ToneComponent, and Multi-Tone Synthesis
=====================================================================
Verifies:
1. Sinusoidal signal evaluation (amplitude, frequency, phase, DC offset).
2. Multi-tone signal synthesis and superposition principle.
3. Dual-tone generation (e.g. DTMF).
4. Harmonic series generation (Fourier square and sawtooth approximations).
5. Theoretical signal metrics (average power, RMS voltage, PAPR, bandwidth).
6. Nyquist sampling rate computation and satisfaction check.
7. Continuous high-resolution waveform generation.
8. Plotter utility execution without errors.
"""

import math
import unittest
from src.analog.continuous_signal import ContinuousSignal, ToneComponent
from src.analog.plotter import plot_continuous_and_sampled


class TestContinuousSignal(unittest.TestCase):
    def test_single_sine_evaluation(self) -> None:
        # A = 2.0, f = 1.0 Hz, phi = 0
        sig = ContinuousSignal.create_simple_sine(amplitude=2.0, frequency=1.0)
        self.assertAlmostEqual(sig.evaluate(0.0), 0.0, places=5)
        self.assertAlmostEqual(sig.evaluate(0.25), 2.0, places=5)
        self.assertAlmostEqual(sig.evaluate(0.5), 0.0, places=5)
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
        self.assertEqual(sig.min_frequency, 5.0)
        self.assertEqual(sig.bandwidth, 10.0)
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

    def test_multitone_creation_and_superposition(self) -> None:
        """Verify multi-tone synthesis matches sum of independent components."""
        # Tone 1: amp 1.0, freq 2.0; Tone 2: amp 0.5, freq 4.0
        sig_multi = ContinuousSignal.create_multitone(
            components=[(1.0, 2.0), (0.5, 4.0, math.pi / 2)],
            dc_offset=0.5,
        )
        t_eval = 0.123
        v_tone1 = 1.0 * math.sin(2.0 * math.pi * 2.0 * t_eval)
        v_tone2 = 0.5 * math.sin(2.0 * math.pi * 4.0 * t_eval + math.pi / 2)
        v_expected = v_tone1 + v_tone2 + 0.5
        self.assertAlmostEqual(sig_multi.evaluate(t_eval), v_expected, places=5)
        self.assertEqual(sig_multi.frequencies, [2.0, 4.0])

    def test_dual_tone_factory(self) -> None:
        """Verify dual-tone factory (e.g. DTMF)."""
        dt_sig = ContinuousSignal.create_dual_tone(
            freq1=697.0, freq2=1209.0, amp1=0.7, amp2=0.7
        )
        self.assertEqual(dt_sig.max_frequency, 1209.0)
        self.assertEqual(dt_sig.nyquist_rate, 2418.0)
        self.assertEqual(len(dt_sig.tones), 2)

    def test_harmonic_series_square_and_sawtooth(self) -> None:
        """Verify harmonic series synthesis for Fourier approximations."""
        # Square wave (odd harmonics)
        sq_sig = ContinuousSignal.create_harmonic_series(
            fundamental_freq=10.0, num_harmonics=3, base_amplitude=1.0, harmonic_type="odd"
        )
        self.assertEqual(len(sq_sig.tones), 3)
        self.assertEqual(sq_sig.tones[0].frequency, 10.0)
        self.assertEqual(sq_sig.tones[1].frequency, 30.0)
        self.assertEqual(sq_sig.tones[2].frequency, 50.0)
        # Amplitudes: 4/(1*pi), 4/(3*pi), 4/(5*pi)
        self.assertAlmostEqual(sq_sig.tones[0].amplitude, 4.0 / math.pi)
        self.assertAlmostEqual(sq_sig.tones[1].amplitude, 4.0 / (3.0 * math.pi))

        # Sawtooth wave (all harmonics)
        saw_sig = ContinuousSignal.create_harmonic_series(
            fundamental_freq=5.0, num_harmonics=4, base_amplitude=1.0, harmonic_type="all"
        )
        self.assertEqual(len(saw_sig.tones), 4)
        self.assertEqual(saw_sig.tones[0].frequency, 5.0)
        self.assertEqual(saw_sig.tones[1].frequency, 10.0)
        self.assertEqual(saw_sig.tones[2].frequency, 15.0)
        self.assertEqual(saw_sig.tones[3].frequency, 20.0)

    def test_signal_metrics_power_rms_papr(self) -> None:
        """Verify theoretical calculations for Average Power, RMS Voltage, and PAPR."""
        # Sig: 2.0*sin(...) + 0.0 offset -> P_avg = 0.5 * (2.0^2) = 2.0 W, V_rms = sqrt(2) ~ 1.414V
        sig1 = ContinuousSignal.create_simple_sine(amplitude=2.0, frequency=1.0)
        self.assertAlmostEqual(sig1.average_power, 2.0, places=5)
        self.assertAlmostEqual(sig1.rms_voltage, math.sqrt(2.0), places=5)
        # Peak amplitude = 2.0 -> PAPR = 4.0 / 2.0 = 2.0
        self.assertAlmostEqual(sig1.peak_to_average_power_ratio, 2.0, places=5)

        # With DC offset: x(t) = 2.0*sin(...) + 1.0 -> P_avg = 1.0^2 + 0.5*(4) = 3.0 W
        sig2 = ContinuousSignal.create_simple_sine(amplitude=2.0, frequency=1.0, dc_offset=1.0)
        self.assertAlmostEqual(sig2.average_power, 3.0, places=5)
        self.assertAlmostEqual(sig2.rms_voltage, math.sqrt(3.0), places=5)

    def test_generate_continuous_waveform(self) -> None:
        """Verify fine continuous grid generation."""
        sig = ContinuousSignal.create_simple_sine(amplitude=1.0, frequency=5.0)
        t_pts, v_pts = sig.generate_continuous_waveform(duration=1.0, points_per_cycle=50)
        # With f_max=5, dt = 1 / (50*5) = 1/250 -> 251 points
        self.assertGreaterEqual(len(t_pts), 250)
        self.assertEqual(len(t_pts), len(v_pts))

    def test_plotter_utility(self) -> None:
        """Verify plotter utility executes without crashing."""
        sig = ContinuousSignal.create_simple_sine(amplitude=1.0, frequency=2.0)
        fig = plot_continuous_and_sampled(sig, sampling_rate=10.0, duration=0.5)
        # fig may be None if matplotlib unavailable, or a Figure if available
        if fig is not None:
            import matplotlib.pyplot as plt
            plt.close(fig)


if __name__ == "__main__":
    unittest.main()
