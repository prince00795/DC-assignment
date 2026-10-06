"""
Continuous Signal Modeling Module
=================================
Models continuous analog signals (single-tone sinusoid or composite multi-tone),
evaluates continuous waveforms x(t), and provides Nyquist-rate sampling infrastructure
for Pulse Code Modulation (PCM) and Delta Modulation (DM).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Sequence


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


class ContinuousSignal:
    """
    Mathematical continuous-time analog signal model x(t).
    Supports single sinusoids or composite multi-tone signals with DC offset.
    """

    def __init__(
        self,
        tones: Sequence[ToneComponent] | None = None,
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

    @property
    def max_frequency(self) -> float:
        """Highest frequency component f_max in Hz."""
        return max(tone.frequency for tone in self.tones)

    @property
    def nyquist_rate(self) -> float:
        """
        Theoretical Nyquist sampling rate: f_nyquist = 2 * f_max.
        Minimum rate to avoid aliasing per the Nyquist-Shannon Sampling Theorem.
        """
        return 2.0 * self.max_frequency

    def is_nyquist_satisfied(self, sampling_rate: float) -> bool:
        """
        Checks whether a given sampling rate satisfies the Nyquist criterion (fs >= 2 * f_max).
        """
        return sampling_rate >= self.nyquist_rate

    def evaluate(self, t: float) -> float:
        """
        Evaluates the continuous analog signal at a specific time t.
        x(t) = sum(A_k * sin(2*pi*f_k*t + phi_k)) + dc_offset
        """
        val = self.dc_offset
        for tone in self.tones:
            val += tone.evaluate(t)
        return val

    def sample(self, sampling_rate: float, duration: float) -> Tuple[List[float], List[float]]:
        """
        Uniformly samples the continuous signal at sampling_rate (Hz) across duration (s).

        :param sampling_rate: Number of samples per second (fs).
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

    def get_peak_amplitude(self) -> float:
        """Returns the theoretical maximum possible peak value |x(t)|."""
        return sum(tone.amplitude for tone in self.tones) + abs(self.dc_offset)
