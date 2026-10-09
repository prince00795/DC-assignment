"""
Unit Tests: Nyquist Sampling & Whittaker-Shannon Reconstruction
===============================================================
Verifies:
1. Theoretical Nyquist rate calculation (fs_nyquist = 2 * f_max).
2. Nyquist criterion validation (oversampling vs undersampling).
3. Sampling modes:
    * Ideal Dirac impulse sampling
    * Flat-top / Zero-Order Hold (ZOH) sampling
    * Natural gated sampling
4. Spectral folding and aliasing frequency detection.
5. Whittaker-Shannon sinc reconstruction:
    * High reconstruction fidelity (low MSE, high SNR) when fs >= 2 * f_max
    * Significant distortion when sub-Nyquist undersampled (fs < 2 * f_max)
6. Parameter validation and error handling.
7. Visualizer functions execution.
"""

import math
import unittest
from src.analog.continuous_signal import ContinuousSignal
from src.analog.sampling import NyquistSampler, SamplingResult
from src.analog.plotter import plot_nyquist_reconstruction


class TestNyquistSampling(unittest.TestCase):
    def setUp(self) -> None:
        self.sampler = NyquistSampler()
        # Single tone 5 Hz: f_max = 5 Hz, f_nyquist = 10 Hz
        self.single_sig = ContinuousSignal.create_simple_sine(amplitude=2.0, frequency=5.0)
        # Multi-tone: 3 Hz and 8 Hz: f_max = 8 Hz, f_nyquist = 16 Hz
        self.multi_sig = ContinuousSignal.create_multitone(
            components=[(2.0, 3.0), (1.5, 8.0, math.pi / 4)],
            dc_offset=0.5,
        )

    def test_nyquist_rate_and_frequency(self) -> None:
        """Verify Nyquist rate (2 * f_max) and folding frequency (fs / 2)."""
        nyq_single = self.sampler.calculate_nyquist_rate(self.single_sig)
        self.assertEqual(nyq_single, 10.0)

        nyq_multi = self.sampler.calculate_nyquist_rate(self.multi_sig)
        self.assertEqual(nyq_multi, 16.0)

    def test_ideal_sampling_points(self) -> None:
        """Verify ideal discrete impulse sample points and timings."""
        duration = 0.5
        fs = 20.0  # Ts = 0.05s, 10 samples
        res = self.sampler.sample(self.single_sig, sampling_rate=fs, duration=duration, mode="ideal")

        self.assertEqual(res.num_samples, 10)
        self.assertAlmostEqual(res.sampling_interval, 0.05)
        self.assertTrue(res.is_nyquist_satisfied)
        self.assertEqual(res.oversampling_ratio, 2.0)

        # Verify sample values match signal evaluations exactly
        for tn, val in zip(res.sample_times, res.sample_values):
            expected = self.single_sig.evaluate(tn)
            self.assertAlmostEqual(val, expected, places=5)

    def test_flat_top_zoh_sampling(self) -> None:
        """Verify Flat-top Zero-Order Hold (ZOH) waveform."""
        duration = 0.2
        fs = 10.0  # Ts = 0.1s -> 2 samples: t=0.0, t=0.1
        res = self.sampler.sample(
            self.single_sig,
            sampling_rate=fs,
            duration=duration,
            mode="flat_top",
            points_per_pulse=10,
        )
        self.assertIsNotNone(res.zoh_times)
        self.assertIsNotNone(res.zoh_values)
        self.assertEqual(len(res.zoh_times), len(res.zoh_values))
        # Within the first pulse [0, 0.1), all zoh_values should equal the first sample
        v0 = res.sample_values[0]
        self.assertTrue(all(v == v0 for v in res.zoh_values[:10]))

    def test_natural_sampling(self) -> None:
        """Verify natural sampling gating pulse behavior."""
        duration = 0.2
        fs = 10.0  # Ts = 0.1s
        tau = 0.04  # 40% pulse width
        res = self.sampler.sample(
            self.single_sig,
            sampling_rate=fs,
            duration=duration,
            mode="natural",
            pulse_width=tau,
            points_per_pulse=10,
        )
        self.assertIsNotNone(res.zoh_times)
        self.assertIsNotNone(res.zoh_values)
        # Check that after tau in each pulse interval, the signal drops to 0
        dt = 0.1 / 10
        # point index 5 is t = 5 * dt = 0.05 > tau (0.04) -> should be 0.0
        self.assertEqual(res.zoh_values[5], 0.0)

    def test_aliasing_detection_and_folding_frequency(self) -> None:
        """Verify spectral folding when undersampling."""
        # Multi-tone: 3 Hz and 8 Hz.
        # If sampled at fs = 10 Hz:
        # Folding frequency f_N = 5 Hz.
        # Tone 1 (3 Hz) <= 5 Hz: no aliasing, apparent = 3 Hz.
        # Tone 2 (8 Hz) > 5 Hz: aliased! Apparent folded frequency = min(8%10, 10 - 8%10) = min(8, 2) = 2 Hz!
        alias_info = self.sampler.detect_aliasing(self.multi_sig, sampling_rate=10.0)
        self.assertFalse(alias_info["is_nyquist_satisfied"])
        self.assertTrue(alias_info["has_aliasing"])
        self.assertEqual(alias_info["folding_frequency"], 5.0)

        folded = alias_info["folded_frequencies"]
        self.assertEqual(folded[3.0], 3.0)
        self.assertEqual(folded[8.0], 2.0)

    def test_whittaker_shannon_reconstruction_oversampled_vs_undersampled(self) -> None:
        """
        Verify that Nyquist oversampled signals reconstruct accurately with low MSE,
        while undersampled signals produce severe aliasing distortion.
        """
        duration = 1.0  # 1 second
        # 1. Oversampled at 4x Nyquist (40 Hz for 5 Hz tone)
        res_over = self.sampler.sample(self.single_sig, sampling_rate=50.0, duration=duration)
        metrics_over = res_over.compute_reconstruction_metrics(self.single_sig, num_eval_points=200)

        # 2. Undersampled at sub-Nyquist (6 Hz < 10 Hz Nyquist rate)
        res_under = self.sampler.sample(self.single_sig, sampling_rate=6.0, duration=duration)
        metrics_under = res_under.compute_reconstruction_metrics(self.single_sig, num_eval_points=200)

        # Oversampled MSE should be dramatically smaller than undersampled MSE
        self.assertLess(metrics_over["mse"], 0.05)
        self.assertGreater(metrics_under["mse"], 0.2)
        self.assertGreater(metrics_over["snr_db"], metrics_under["snr_db"])

    def test_sample_at_nyquist_convenience_method(self) -> None:
        """Verify sample_at_nyquist with multipliers."""
        res_crit = self.sampler.sample_at_nyquist(self.single_sig, duration=0.5, multiplier=1.0)
        self.assertEqual(res_crit.sampling_rate, 10.0)
        self.assertTrue(res_crit.is_nyquist_satisfied)

        res_over = self.sampler.sample_at_nyquist(self.single_sig, duration=0.5, multiplier=2.5)
        self.assertEqual(res_over.sampling_rate, 25.0)
        self.assertEqual(res_over.oversampling_ratio, 2.5)

    def test_reconstruct_waveform_helper(self) -> None:
        """Verify reconstruct_waveform generates grid of requested length."""
        res = self.sampler.sample(self.single_sig, sampling_rate=30.0, duration=0.5)
        times, values = self.sampler.reconstruct_waveform(res, num_points=100)
        self.assertEqual(len(times), 100)
        self.assertEqual(len(values), 100)

    def test_invalid_parameters_and_inputs(self) -> None:
        """Verify exception handling on invalid sampler inputs."""
        with self.assertRaises(ValueError):
            self.sampler.sample(self.single_sig, sampling_rate=0.0, duration=1.0)
        with self.assertRaises(ValueError):
            self.sampler.sample(self.single_sig, sampling_rate=-5.0, duration=1.0)
        with self.assertRaises(ValueError):
            self.sampler.sample(self.single_sig, sampling_rate=20.0, duration=-1.0)
        with self.assertRaises(ValueError):
            self.sampler.sample(self.single_sig, sampling_rate=20.0, duration=1.0, mode="invalid_mode")
        with self.assertRaises(ValueError):
            # tau > Ts (Ts = 0.1, tau = 0.15)
            self.sampler.sample(self.single_sig, sampling_rate=10.0, duration=1.0, pulse_width=0.15)
        with self.assertRaises(ValueError):
            self.sampler.sample_at_nyquist(self.single_sig, duration=1.0, multiplier=-1.0)

    def test_plotter_reconstruction_utility(self) -> None:
        """Verify plot_nyquist_reconstruction produces a figure."""
        res = self.sampler.sample(self.single_sig, sampling_rate=25.0, duration=0.2)
        fig = plot_nyquist_reconstruction(self.single_sig, res)
        self.assertIsNotNone(fig)


if __name__ == "__main__":
    unittest.main()
