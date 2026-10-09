"""
Nyquist Sampling Module
=======================
Implements comprehensive Nyquist-Shannon sampling theory and continuous-to-discrete conversion:
- Nyquist criterion verification: fs >= 2 * f_max (Nyquist rate).
- Multiple sampling modes:
    * Ideal Impulse Sampling: x_s[n] = x(n * Ts)
    * Flat-Top Sampling (Zero-Order Hold / ZOH): Pulse amplitude modulation with sample hold
    * Natural Sampling: Finite-width gating pulses
- Aliasing detection & spectral folding analysis:
    * Calculates apparent folded alias frequencies when fs < 2 * f_max
- Whittaker-Shannon Sinc Interpolation (DAC continuous reconstruction):
    * Reconstructs continuous x(t) from discrete samples x[n]
    * Computes reconstruction error metrics (MSE, RMSE, Max Error, SNR/SNDR in dB)
    * Demonstrates exact reconstruction when fs >= 2 * f_max vs aliasing distortion when undersampled.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple
from src.analog.continuous_signal import ContinuousSignal


@dataclass
class SamplingResult:
    """
    Encapsulates the discrete output and diagnostic metrics of a sampling process.
    """
    sample_times: List[float]
    sample_values: List[float]
    sampling_rate: float          # fs in Hz
    duration: float               # Duration in seconds
    nyquist_rate: float           # 2 * f_max in Hz
    is_nyquist_satisfied: bool    # True if fs >= 2 * f_max
    oversampling_ratio: float     # fs / (2 * f_max)
    sampling_mode: str = "ideal"  # 'ideal', 'flat_top', or 'natural'
    pulse_width: Optional[float] = None
    aliasing_info: Dict[str, Any] = field(default_factory=dict)
    zoh_times: Optional[List[float]] = None
    zoh_values: Optional[List[float]] = None

    @property
    def num_samples(self) -> int:
        """Total number of discrete samples captured."""
        return len(self.sample_values)

    @property
    def sampling_interval(self) -> float:
        """Time between adjacent samples Ts = 1 / fs."""
        return 1.0 / self.sampling_rate

    @property
    def nyquist_frequency(self) -> float:
        """Nyquist folding frequency f_N = fs / 2."""
        return self.sampling_rate / 2.0

    def reconstruct_sinc(self, eval_times: Sequence[float]) -> List[float]:
        """
        Reconstructs the continuous-time signal from discrete samples using the
        ideal Whittaker-Shannon interpolation formula:
            x_hat(t) = sum_{n=0}^{N-1} x[n] * sinc((t - n*Ts) / Ts)
        where sinc(u) = sin(pi * u) / (pi * u) with sinc(0) = 1.

        :param eval_times: Sequence of time instants at which to reconstruct x_hat(t).
        :return: Reconstructed continuous signal values at eval_times.
        """
        ts = self.sampling_interval
        n_samples = len(self.sample_values)
        reconstructed: List[float] = []

        for t in eval_times:
            val = 0.0
            for n in range(n_samples):
                tn = self.sample_times[n]
                u = (t - tn) / ts
                if abs(u) < 1e-12:
                    sinc_val = 1.0
                else:
                    pi_u = math.pi * u
                    sinc_val = math.sin(pi_u) / pi_u
                val += self.sample_values[n] * sinc_val
            reconstructed.append(val)

        return reconstructed

    def compute_reconstruction_metrics(
        self,
        original_signal: ContinuousSignal,
        num_eval_points: int = 400,
        margin: float = 0.1,
    ) -> Dict[str, float]:
        """
        Computes reconstruction accuracy metrics against the ground truth continuous signal.

        Evaluates over the central region [margin * duration, (1 - margin) * duration]
        to avoid truncation boundary artifacts inherent in finite-length sinc summation.

        :param original_signal: Original continuous signal model.
        :param num_eval_points: Number of high-resolution test points.
        :param margin: Fraction of duration to exclude from edges (default 0.10).
        :return: Dict containing MSE, RMSE, MaxError, and SNR_dB.
        """
        t_start = self.duration * margin
        t_end = self.duration * (1.0 - margin)
        if t_end <= t_start:
            t_start, t_end = 0.0, self.duration

        dt = (t_end - t_start) / max(num_eval_points - 1, 1)
        eval_times = [t_start + i * dt for i in range(num_eval_points)]

        true_values = [original_signal.evaluate(t) for t in eval_times]
        recon_values = self.reconstruct_sinc(eval_times)

        errors = [r - y for r, y in zip(recon_values, true_values)]
        mse = sum(e ** 2 for e in errors) / len(errors)
        rmse = math.sqrt(mse)
        max_error = max(abs(e) for e in errors)

        # Signal power for SNR
        sig_power = sum(y ** 2 for y in true_values) / len(true_values)
        if mse > 1e-12 and sig_power > 1e-12:
            snr_db = 10.0 * math.log10(sig_power / mse)
        elif mse <= 1e-12:
            snr_db = 120.0  # Near-infinite SNR
        else:
            snr_db = 0.0

        return {
            "mse": mse,
            "rmse": rmse,
            "max_error": max_error,
            "snr_db": snr_db,
        }

    def summary(self) -> str:
        """Formatted string summary of sampling results and Nyquist conditions."""
        status = "Nyquist Satisfied (fs >= 2*f_max)" if self.is_nyquist_satisfied else "ALIENATING / Under-sampled (fs < 2*f_max)"
        lines = [
            f"SamplingResult [Mode: {self.sampling_mode.upper()}, Status: {status}]",
            f" - Sampling Rate (fs):        {self.sampling_rate:.2f} Hz",
            f" - Nyquist Rate (2 * f_max):  {self.nyquist_rate:.2f} Hz",
            f" - Oversampling Ratio (OSR):  {self.oversampling_ratio:.2f}x",
            f" - Sampling Interval (Ts):    {self.sampling_interval * 1000:.2f} ms",
            f" - Total Samples Captured:    {self.num_samples}",
            f" - Nyquist Frequency (fs/2):  {self.nyquist_frequency:.2f} Hz",
        ]
        if not self.is_nyquist_satisfied and "folded_frequencies" in self.aliasing_info:
            lines.append(" - Aliased Components:")
            for orig_f, folded_f in self.aliasing_info["folded_frequencies"].items():
                lines.append(f"    * Original {orig_f:.2f} Hz -> Aliased Apparent {folded_f:.2f} Hz")
        return "\n".join(lines)


class NyquistSampler:
    """
    Nyquist Sampling Engine.
    Samples continuous analog signals under various modes, detects aliasing,
    and performs Whittaker-Shannon reconstruction.
    """

    @staticmethod
    def calculate_nyquist_rate(signal: ContinuousSignal) -> float:
        """
        Calculates the theoretical minimum Nyquist sampling rate: f_nyquist = 2 * f_max.

        :param signal: ContinuousSignal instance.
        :return: Nyquist rate in Hz.
        """
        return signal.nyquist_rate

    @staticmethod
    def detect_aliasing(signal: ContinuousSignal, sampling_rate: float) -> Dict[str, Any]:
        """
        Analyzes spectral folding and detects aliasing distortion for a given sampling rate.

        When fs < 2 * f_max, frequencies above fs/2 fold back into the baseband [0, fs/2].
        The apparent alias frequency is:
            f_alias = min(f % fs, fs - (f % fs))

        :param signal: ContinuousSignal instance.
        :param sampling_rate: Sampling frequency fs in Hz.
        :return: Dictionary containing aliasing diagnostics.
        """
        if sampling_rate <= 0:
            raise ValueError(f"Sampling rate must be positive, got {sampling_rate}")

        f_nyquist = signal.nyquist_rate
        f_folding = sampling_rate / 2.0
        is_satisfied = sampling_rate >= f_nyquist

        folded_frequencies: Dict[float, float] = {}
        has_aliasing = False

        for tone in signal.tones:
            f_orig = tone.frequency
            if f_orig > f_folding:
                has_aliasing = True
                # Apparent frequency in baseband [0, fs/2]
                mod = f_orig % sampling_rate
                f_alias = min(mod, sampling_rate - mod)
                folded_frequencies[f_orig] = round(f_alias, 4)
            else:
                folded_frequencies[f_orig] = f_orig

        return {
            "is_nyquist_satisfied": is_satisfied,
            "has_aliasing": has_aliasing,
            "nyquist_rate": f_nyquist,
            "folding_frequency": f_folding,
            "oversampling_ratio": sampling_rate / f_nyquist if f_nyquist > 0 else float("inf"),
            "folded_frequencies": folded_frequencies,
        }

    def sample(
        self,
        signal: ContinuousSignal,
        sampling_rate: float,
        duration: float,
        mode: str = "ideal",
        pulse_width: Optional[float] = None,
        points_per_pulse: int = 20,
    ) -> SamplingResult:
        """
        Samples a ContinuousSignal using the designated sampling technique.

        :param signal: ContinuousSignal model to sample.
        :param sampling_rate: Sampling frequency fs (Hz).
        :param duration: Total signal duration (seconds).
        :param mode:
            - 'ideal': Discrete impulse train sampling x[n] = x(n * Ts).
            - 'flat_top': Zero-Order Hold (ZOH) PAM. Holds sample level across bit interval.
            - 'natural': Gated natural sampling with finite pulse width tau.
        :param pulse_width: Pulse width tau in seconds (required for 'natural', optional for 'flat_top').
                            Defaults to 0.5 * Ts if not provided.
        :param points_per_pulse: Time resolution for continuous ZOH / flat-top waveform generation.
        :return: SamplingResult dataclass.
        """
        if sampling_rate <= 0:
            raise ValueError(f"Sampling rate must be positive, got {sampling_rate}")
        if duration <= 0:
            raise ValueError(f"Duration must be positive, got {duration}")

        valid_modes = ("ideal", "flat_top", "natural")
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}', must be one of {valid_modes}")

        ts = 1.0 / sampling_rate
        tau = pulse_width if pulse_width is not None else (0.5 * ts)
        if tau > ts:
            raise ValueError(f"Pulse width tau ({tau}s) cannot exceed sampling interval Ts ({ts}s)")

        # Uniform sample times
        num_samples = int(math.ceil(duration * sampling_rate))
        sample_times = [n * ts for n in range(num_samples)]
        sample_values = [signal.evaluate(t) for t in sample_times]

        aliasing_info = self.detect_aliasing(signal, sampling_rate)

        zoh_times: Optional[List[float]] = None
        zoh_values: Optional[List[float]] = None

        if mode == "flat_top":
            # Generate staircase Zero-Order Hold waveform
            zoh_times = []
            zoh_values = []
            dt = ts / points_per_pulse
            for n, (tn, val) in enumerate(zip(sample_times, sample_values)):
                for p in range(points_per_pulse):
                    t = tn + p * dt
                    if t <= duration:
                        zoh_times.append(t)
                        zoh_values.append(val)

        elif mode == "natural":
            # Natural sampling: transmits true signal during [n*Ts, n*Ts + tau], zero elsewhere
            zoh_times = []
            zoh_values = []
            dt = ts / points_per_pulse
            for n, (tn, val) in enumerate(zip(sample_times, sample_values)):
                for p in range(points_per_pulse):
                    t = tn + p * dt
                    if t <= duration:
                        zoh_times.append(t)
                        if (t - tn) <= tau:
                            zoh_values.append(signal.evaluate(t))
                        else:
                            zoh_values.append(0.0)

        return SamplingResult(
            sample_times=sample_times,
            sample_values=sample_values,
            sampling_rate=sampling_rate,
            duration=duration,
            nyquist_rate=signal.nyquist_rate,
            is_nyquist_satisfied=aliasing_info["is_nyquist_satisfied"],
            oversampling_ratio=aliasing_info["oversampling_ratio"],
            sampling_mode=mode,
            pulse_width=tau if mode in ("flat_top", "natural") else None,
            aliasing_info=aliasing_info,
            zoh_times=zoh_times,
            zoh_values=zoh_values,
        )

    def sample_at_nyquist(
        self,
        signal: ContinuousSignal,
        duration: float,
        multiplier: float = 1.0,
        mode: str = "ideal",
    ) -> SamplingResult:
        """
        Convenience sampler relative to the theoretical Nyquist rate:
        fs = multiplier * (2 * f_max).

        :param signal: ContinuousSignal instance.
        :param duration: Duration in seconds.
        :param multiplier: Multiplier factor:
            - 1.0: Critical Nyquist rate (fs = 2 * f_max)
            - > 1.0 (e.g. 2.0, 4.0): Oversampling (fs > 2 * f_max)
            - < 1.0 (e.g. 0.5): Undersampling with deliberate aliasing (fs < 2 * f_max)
        :param mode: Sampling mode ('ideal', 'flat_top', 'natural').
        :return: SamplingResult.
        """
        if multiplier <= 0:
            raise ValueError(f"Multiplier must be positive, got {multiplier}")

        fs = multiplier * signal.nyquist_rate
        return self.sample(signal=signal, sampling_rate=fs, duration=duration, mode=mode)

    def reconstruct_waveform(
        self,
        result: SamplingResult,
        num_points: int = 500,
    ) -> Tuple[List[float], List[float]]:
        """
        Reconstructs a smooth continuous waveform from discrete samples using sinc interpolation.

        :param result: SamplingResult instance.
        :param num_points: Number of evaluation points along the duration.
        :return: Tuple of (eval_times, reconstructed_voltages).
        """
        dt = result.duration / max(num_points - 1, 1)
        eval_times = [i * dt for i in range(num_points)]
        reconstructed_voltages = result.reconstruct_sinc(eval_times)
        return eval_times, reconstructed_voltages
