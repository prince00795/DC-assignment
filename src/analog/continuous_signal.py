"""
Continuous Signal Modeling Module
=================================
Models continuous analog signals:
- Single-tone sinusoids: x(t) = A * sin(2 * pi * f * t + phase) + DC
- Composite multi-tone analog waveforms: x(t) = sum(A_k * sin(2 * pi * f_k * t + phi_k)) + DC
- Harmonic synthesis: Fourier series approximations for square and sawtooth waves
- Dual-tone signaling: Telephony DTMF / multi-frequency synthesis
- Signal metrics: Maximum frequency, Nyquist sampling rate, Average Power, RMS Voltage, PAPR
- Continuous and discrete Nyquist sampling infrastructure for PCM and Delta Modulation.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple, Union


@dataclass
class ToneComponent:
    """Represents a sinusoidal tone: A * sin(2 * pi * f * t + phase)."""
    amplitude: float = 1.0
    frequency: float = 1.0  # Hz
    phase: float = 0.0      # Radians

    def __post_init__(self) -> None:
        if self.frequency < 0:
            raise ValueError(f"Frequency must be non-negative, got {self.frequency}")
        if self.amplitude < 0:
            raise ValueError(f"Amplitude must be non-negative, got {self.amplitude}")

    def evaluate(self, t: float) -> float:
        """Evaluate the tone at time t."""
        return self.amplitude * math.sin(2.0 * math.pi * self.frequency * t + self.phase)

    def __str__(self) -> str:
        return f"{self.amplitude:.2f} * sin(2*pi*{self.frequency:.2f}*t + {self.phase:.2f})"

    def __repr__(self) -> str:
        return f"ToneComponent(amp={self.amplitude:.2f}, freq={self.frequency:.2f}Hz, phase={self.phase:.2f}rad)"


# Type alias for flexible multi-tone specifications: ToneComponent or (amp, freq) or (amp, freq, phase)
ToneSpec = Union[ToneComponent, Tuple[float, float], Tuple[float, float, float]]


class ContinuousSignal:
    """
    Mathematical continuous-time analog signal model x(t).
    Supports single sinusoids, multi-tone composite signals, harmonic series, and DC offset.
    """

    def __init__(
        self,
        tones: Optional[Sequence[ToneComponent]] = None,
        dc_offset: float = 0.0,
    ) -> None:
        """
        Initialize the analog signal.

        :param tones: List of ToneComponents. If None, defaults to single 1.0V, 1.0Hz tone.
        :param dc_offset: Constant DC level added to the signal.
        """
        if tones is None:
            self.tones: List[ToneComponent] = [ToneComponent(amplitude=1.0, frequency=1.0, phase=0.0)]
        else:
            self.tones = list(tones)
            if not self.tones:
                raise ValueError("Signal must have at least one frequency component.")

        self.dc_offset = dc_offset

    @classmethod
    def create_simple_sine(
        cls,
        amplitude: float = 1.0,
        frequency: float = 1.0,
        phase: float = 0.0,
        dc_offset: float = 0.0,
    ) -> ContinuousSignal:
        """Convenience factory for a standard single sinusoidal waveform."""
        return cls(
            tones=[ToneComponent(amplitude=amplitude, frequency=frequency, phase=phase)],
            dc_offset=dc_offset,
        )

    @classmethod
    def create_multitone(
        cls,
        components: Sequence[ToneSpec],
        dc_offset: float = 0.0,
    ) -> ContinuousSignal:
        """
        Factory for composite multi-tone signals.

        :param components: Sequence of ToneComponents or tuples (amp, freq) or (amp, freq, phase).
        :param dc_offset: DC bias voltage.
        :return: ContinuousSignal with combined tones.
        """
        if not components:
            raise ValueError("components list cannot be empty.")

        tones: List[ToneComponent] = []
        for c in components:
            if isinstance(c, ToneComponent):
                tones.append(c)
            elif isinstance(c, (tuple, list)):
                if len(c) == 2:
                    tones.append(ToneComponent(amplitude=float(c[0]), frequency=float(c[1]), phase=0.0))
                elif len(c) == 3:
                    tones.append(ToneComponent(amplitude=float(c[0]), frequency=float(c[1]), phase=float(c[2])))
                else:
                    raise ValueError(f"Invalid component tuple length: {c}")
            else:
                raise TypeError(f"Unsupported component type: {type(c)}")

        return cls(tones=tones, dc_offset=dc_offset)

    @classmethod
    def create_dual_tone(
        cls,
        freq1: float,
        freq2: float,
        amp1: float = 1.0,
        amp2: float = 1.0,
        phase1: float = 0.0,
        phase2: float = 0.0,
        dc_offset: float = 0.0,
    ) -> ContinuousSignal:
        """
        Factory for a dual-tone signal (e.g., DTMF telecommunication tones).

        :param freq1: Frequency of tone 1 in Hz.
        :param freq2: Frequency of tone 2 in Hz.
        :param amp1: Amplitude of tone 1.
        :param amp2: Amplitude of tone 2.
        :param phase1: Phase of tone 1 in radians.
        :param phase2: Phase of tone 2 in radians.
        :param dc_offset: Constant DC level.
        :return: ContinuousSignal instance.
        """
        return cls(
            tones=[
                ToneComponent(amplitude=amp1, frequency=freq1, phase=phase1),
                ToneComponent(amplitude=amp2, frequency=freq2, phase=phase2),
            ],
            dc_offset=dc_offset,
        )

    @classmethod
    def create_harmonic_series(
        cls,
        fundamental_freq: float,
        num_harmonics: int,
        base_amplitude: float = 1.0,
        harmonic_type: str = "odd",
        dc_offset: float = 0.0,
    ) -> ContinuousSignal:
        """
        Synthesizes a periodic waveform from its Fourier harmonic components.

        :param fundamental_freq: Fundamental frequency f0 in Hz.
        :param num_harmonics: Number of harmonic components to include (>= 1).
        :param base_amplitude: Fundamental amplitude scale A.
        :param harmonic_type:
            - 'odd': Odd harmonics (1, 3, 5, ...) -> Fourier square wave approximation: A_k = (4*A) / (pi * k)
            - 'all': All harmonics (1, 2, 3, ...) -> Fourier sawtooth approximation: A_k = (2*A) / (pi * k)
            - 'even': Even harmonics only (2, 4, 6, ...)
        :param dc_offset: DC bias.
        :return: ContinuousSignal instance.
        """
        if fundamental_freq <= 0:
            raise ValueError(f"fundamental_freq must be positive, got {fundamental_freq}")
        if num_harmonics <= 0:
            raise ValueError(f"num_harmonics must be positive, got {num_harmonics}")

        tones: List[ToneComponent] = []

        if harmonic_type == "odd":
            # Square wave: x(t) = sum_{m=0}^{N-1} [4A / (pi*(2m+1))] * sin(2*pi*(2m+1)*f0*t)
            for m in range(num_harmonics):
                k = 2 * m + 1
                amp = (4.0 * base_amplitude) / (math.pi * k)
                freq = k * fundamental_freq
                tones.append(ToneComponent(amplitude=amp, frequency=freq, phase=0.0))
        elif harmonic_type == "all":
            # Sawtooth: x(t) = sum_{k=1}^N [2A / (pi*k)] * sin(2*pi*k*f0*t)
            for k in range(1, num_harmonics + 1):
                amp = (2.0 * base_amplitude) / (math.pi * k)
                freq = k * fundamental_freq
                tones.append(ToneComponent(amplitude=amp, frequency=freq, phase=0.0))
        elif harmonic_type == "even":
            for m in range(1, num_harmonics + 1):
                k = 2 * m
                amp = base_amplitude / k
                freq = k * fundamental_freq
                tones.append(ToneComponent(amplitude=amp, frequency=freq, phase=0.0))
        else:
            raise ValueError(f"Unknown harmonic_type '{harmonic_type}', expected 'odd', 'all', or 'even'")

        return cls(tones=tones, dc_offset=dc_offset)

    @property
    def max_frequency(self) -> float:
        """Highest frequency component f_max in Hz."""
        return max(tone.frequency for tone in self.tones)

    @property
    def min_frequency(self) -> float:
        """Lowest frequency component f_min in Hz."""
        return min(tone.frequency for tone in self.tones)

    @property
    def bandwidth(self) -> float:
        """Bandwidth of the signal: f_max - f_min in Hz."""
        return self.max_frequency - self.min_frequency

    @property
    def frequencies(self) -> List[float]:
        """Sorted list of unique frequencies present in the signal."""
        return sorted(list(set(tone.frequency for tone in self.tones)))

    @property
    def nyquist_rate(self) -> float:
        """
        Theoretical Nyquist sampling rate: f_nyquist = 2 * f_max.
        Minimum rate required to avoid aliasing per the Nyquist-Shannon Sampling Theorem.
        """
        return 2.0 * self.max_frequency

    def is_nyquist_satisfied(self, sampling_rate: float) -> bool:
        """Checks whether a given sampling rate satisfies the Nyquist criterion (fs >= 2 * f_max)."""
        return sampling_rate >= self.nyquist_rate

    @property
    def average_power(self) -> float:
        """
        Theoretical average power: P_avg = V_dc^2 + 0.5 * sum(A_k^2).
        For distinct orthogonal sinusoidal tones.
        """
        return (self.dc_offset ** 2) + 0.5 * sum(tone.amplitude ** 2 for tone in self.tones)

    @property
    def rms_voltage(self) -> float:
        """Theoretical Root-Mean-Square (RMS) voltage: V_rms = sqrt(P_avg)."""
        return math.sqrt(self.average_power)

    def get_peak_amplitude(self) -> float:
        """Returns the theoretical maximum upper bound of |x(t)|."""
        return sum(tone.amplitude for tone in self.tones) + abs(self.dc_offset)

    @property
    def peak_to_average_power_ratio(self) -> float:
        """
        Peak-to-Average Power Ratio (PAPR) in linear scale:
        PAPR = (Peak Amplitude)^2 / Average Power.
        """
        p_avg = self.average_power
        if p_avg == 0:
            return 0.0
        return (self.get_peak_amplitude() ** 2) / p_avg

    def evaluate(self, t: float) -> float:
        """
        Evaluates the continuous analog signal at a specific time instant t.
        x(t) = sum(A_k * sin(2*pi*f_k*t + phi_k)) + dc_offset
        """
        val = self.dc_offset
        for tone in self.tones:
            val += tone.evaluate(t)
        return val

    def sample(self, sampling_rate: float, duration: float) -> Tuple[List[float], List[float]]:
        """
        Uniformly samples the continuous signal at sampling_rate (Hz) across duration (s).

        :param sampling_rate: Discrete samples per second (fs).
        :param duration: Total signal duration in seconds.
        :return: Tuple of (sample_times, sample_values).
        """
        if sampling_rate <= 0:
            raise ValueError(f"Sampling rate must be positive, got {sampling_rate}")
        if duration <= 0:
            raise ValueError(f"Duration must be positive, got {duration}")

        dt = 1.0 / sampling_rate
        num_samples = int(math.ceil(duration * sampling_rate))

        sample_times = [k * dt for k in range(num_samples)]
        sample_values = [self.evaluate(t) for t in sample_times]

        return sample_times, sample_values

    def generate_continuous_waveform(
        self,
        duration: float,
        points_per_cycle: int = 100,
    ) -> Tuple[List[float], List[float]]:
        """
        Generates high-resolution time points and voltages for smooth continuous plotting.

        :param duration: Time window duration in seconds.
        :param points_per_cycle: Resolution factor relative to highest frequency.
        :return: Tuple of (time_points, values).
        """
        if duration <= 0:
            raise ValueError(f"Duration must be positive, got {duration}")
        if points_per_cycle <= 1:
            raise ValueError(f"points_per_cycle must be at least 2, got {points_per_cycle}")

        f_max = max(self.max_frequency, 1.0)
        dt = 1.0 / (points_per_cycle * f_max)
        num_points = int(math.ceil(duration / dt)) + 1

        t_pts = [i * dt for i in range(num_points)]
        v_pts = [self.evaluate(t) for t in t_pts]
        return t_pts, v_pts

    def summary(self) -> str:
        """Generates a detailed summary of the continuous signal parameters."""
        lines = [
            f"ContinuousSignal [Tones: {len(self.tones)}, DC Offset: {self.dc_offset:+.2f}V]",
            f" - Maximum Frequency (f_max):     {self.max_frequency:.2f} Hz",
            f" - Minimum Frequency (f_min):     {self.min_frequency:.2f} Hz",
            f" - Signal Bandwidth:              {self.bandwidth:.2f} Hz",
            f" - Theoretical Nyquist Rate (fs): {self.nyquist_rate:.2f} Hz",
            f" - Peak Amplitude Upper Bound:    {self.get_peak_amplitude():.2f} V",
            f" - Average Power (P_avg):         {self.average_power:.3f} W (normalized)",
            f" - RMS Voltage (V_rms):           {self.rms_voltage:.3f} V",
            f" - PAPR (Linear):                 {self.peak_to_average_power_ratio:.2f}",
            " - Constituent Tones:",
        ]
        for idx, tone in enumerate(self.tones):
            lines.append(f"    [{idx + 1}] {tone}")
        return "\n".join(lines)
