"""
Line Coding Base Module
=======================
Defines base abstractions and physical signal data models for all
line encoding and decoding schemes (NRZ-L, NRZ-I, Manchester, AMI, B8ZS, HDB3).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SignalWaveform:
    """
    Physical continuous/discrete signal representation of a transmission waveform.
    Stores voltage samples V(t) over discrete time points t.
    """
    bits: str
    time_points: List[float]
    voltages: List[float]
    samples_per_bit: int = 100
    bit_duration: float = 1.0  # seconds per bit interval Tb
    positive_voltage: float = 1.0
    negative_voltage: float = -1.0
    zero_voltage: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.time_points) != len(self.voltages):
            raise ValueError(
                f"Mismatch: time_points length ({len(self.time_points)}) != "
                f"voltages length ({len(self.voltages)})"
            )

    @property
    def total_duration(self) -> float:
        """Total duration of the transmission in seconds."""
        return len(self.bits) * self.bit_duration

    @property
    def num_bits(self) -> int:
        """Total number of bits in the encoded stream."""
        return len(self.bits)

    @property
    def total_samples(self) -> int:
        """Total number of sampled physical points."""
        return len(self.voltages)

    def get_bit_slice(self, bit_index: int) -> Tuple[List[float], List[float]]:
        """
        Extract the time and voltage arrays corresponding to a specific bit interval.

        :param bit_index: 0-indexed bit index.
        :return: Tuple of (times, voltages) for that bit interval.
        """
        if bit_index < 0 or bit_index >= self.num_bits:
            raise IndexError(f"Bit index {bit_index} out of range [0, {self.num_bits - 1}]")

        start = bit_index * self.samples_per_bit
        end = start + self.samples_per_bit
        return self.time_points[start:end], self.voltages[start:end]

    def get_midpoint_sample(self, bit_index: int) -> Tuple[float, float]:
        """
        Samples the waveform at the exact center of the bit duration:
        t_center = (bit_index + 0.5) * bit_duration.
        Crucial for receiver clock recovery and physical decoding.

        :param bit_index: 0-indexed bit position.
        :return: (time_center, voltage_center)
        """
        if bit_index < 0 or bit_index >= self.num_bits:
            raise IndexError(f"Bit index {bit_index} out of range [0, {self.num_bits - 1}]")

        mid_idx = bit_index * self.samples_per_bit + (self.samples_per_bit // 2)
        return self.time_points[mid_idx], self.voltages[mid_idx]


class LineEncoder(ABC):
    """
    Abstract base class for all line coding schemes.
    Enforces a consistent interface across NRZ-L, NRZ-I, Manchester, Diff Manchester, and AMI.
    """

    def __init__(
        self,
        samples_per_bit: int = 100,
        bit_duration: float = 1.0,
        positive_voltage: float = 1.0,
        negative_voltage: float = -1.0,
        zero_voltage: float = 0.0,
    ) -> None:
        """
        Configure physical electrical parameters for the encoder.

        :param samples_per_bit: Discrete samples evaluated per bit interval (time resolution).
        :param bit_duration: Duration Tb of each bit in seconds.
        :param positive_voltage: High voltage level +V.
        :param negative_voltage: Low/negative voltage level -V.
        :param zero_voltage: Ground level 0V.
        """
        if samples_per_bit < 2:
            raise ValueError(f"samples_per_bit must be at least 2, got {samples_per_bit}")
        if bit_duration <= 0:
            raise ValueError(f"bit_duration must be positive, got {bit_duration}")

        self.samples_per_bit = samples_per_bit
        self.bit_duration = bit_duration
        self.positive_voltage = positive_voltage
        self.negative_voltage = negative_voltage
        self.zero_voltage = zero_voltage

    @property
    @abstractmethod
    def scheme_name(self) -> str:
        """Name of the line coding scheme."""
        pass

    @abstractmethod
    def encode(self, bits: str) -> SignalWaveform:
        """
        Encodes a binary string into a physical SignalWaveform.

        :param bits: String of '0' and '1' characters.
        :return: Encoded SignalWaveform object containing t and V(t).
        """
        pass

    def _validate_input(self, bits: str) -> None:
        """Helper to ensure input is non-empty and strictly binary."""
        if not bits:
            raise ValueError("Input bitstream cannot be empty.")
        if any(c not in ("0", "1") for c in bits):
            raise ValueError(f"Input bitstream contains non-binary characters: {bits}")
