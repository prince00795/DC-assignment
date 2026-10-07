"""
Line Coding Encoders Module
===========================
Implements physical line coding encoders and decoders:
- NRZ-L (Non-Return-to-Zero-Level): Maps binary bits directly to discrete voltage levels (+V, -V).
  Supports both standard telecom convention (0 -> +V, 1 -> -V) and inverted mapping (0 -> -V, 1 -> +V).
- Mid-point physical sampling decoder for bit recovery and verification.
"""

from __future__ import annotations
from typing import Dict, List, Optional
from src.line_coding.base import LineEncoder, SignalWaveform


class NRZLEncoder(LineEncoder):
    """
    Non-Return-to-Zero-Level (NRZ-L) Line Encoder & Decoder.

    In NRZ-L, the signal voltage maintains a constant level (+V or -V) throughout
    the entire bit duration Tb without returning to zero at mid-bit.
    
    Conventions:
    - Standard Telecom / Textbook Convention (zero_is_positive=True):
        Bit '0' -> Positive Voltage (+V)
        Bit '1' -> Negative Voltage (-V)
    - Inverted Convention (zero_is_positive=False):
        Bit '0' -> Negative Voltage (-V)
        Bit '1' -> Positive Voltage (+V)
    """

    def __init__(
        self,
        samples_per_bit: int = 100,
        bit_duration: float = 1.0,
        positive_voltage: float = 1.0,
        negative_voltage: float = -1.0,
        zero_voltage: float = 0.0,
        zero_is_positive: bool = True,
    ) -> None:
        """
        Initialize the NRZ-L Encoder.

        :param samples_per_bit: Number of discrete time samples evaluated per bit interval.
        :param bit_duration: Bit duration Tb in seconds.
        :param positive_voltage: High voltage level +V (default: +1.0V).
        :param negative_voltage: Low voltage level -V (default: -1.0V).
        :param zero_voltage: Reference ground level (default: 0.0V).
        :param zero_is_positive: If True, '0' maps to +V and '1' to -V.
                                 If False, '0' maps to -V and '1' to +V.
        """
        super().__init__(
            samples_per_bit=samples_per_bit,
            bit_duration=bit_duration,
            positive_voltage=positive_voltage,
            negative_voltage=negative_voltage,
            zero_voltage=zero_voltage,
        )
        if positive_voltage <= negative_voltage:
            raise ValueError(
                f"positive_voltage ({positive_voltage}) must be greater than negative_voltage ({negative_voltage})"
            )
        self.zero_is_positive = zero_is_positive

    @property
    def scheme_name(self) -> str:
        """Name of the line coding scheme."""
        return "NRZ-L"

    def bit_to_voltage(self, bit: str) -> float:
        """
        Maps a single binary bit ('0' or '1') to its corresponding physical voltage level.

        :param bit: '0' or '1'
        :return: Floating point voltage (+V or -V)
        """
        if bit == "0":
            return self.positive_voltage if self.zero_is_positive else self.negative_voltage
        elif bit == "1":
            return self.negative_voltage if self.zero_is_positive else self.positive_voltage
        else:
            raise ValueError(f"Invalid bit '{bit}', expected '0' or '1'")

    def voltage_to_bit(self, voltage: float) -> str:
        """
        Classifies a sampled physical voltage back into a binary bit using decision thresholding.

        Decision boundary: V_th = (V_+ + V_-) / 2.

        :param voltage: Sampled voltage.
        :return: '0' or '1'
        """
        threshold = (self.positive_voltage + self.negative_voltage) / 2.0
        if voltage >= threshold:
            return "0" if self.zero_is_positive else "1"
        else:
            return "1" if self.zero_is_positive else "0"

    def encode(self, bits: str) -> SignalWaveform:
        """
        Encodes a binary bitstream into a continuous/discrete SignalWaveform object.

        :param bits: Binary string (e.g., "010011").
        :return: SignalWaveform with discrete time points and voltage levels.
        """
        self._validate_input(bits)

        time_points: List[float] = []
        voltages: List[float] = []
        dt = self.bit_duration / self.samples_per_bit
        num_bits = len(bits)

        transitions = 0
        for i, bit in enumerate(bits):
            level = self.bit_to_voltage(bit)
            bit_start_time = i * self.bit_duration
            
            # Count transition if bit level changes from previous bit
            if i > 0 and bit != bits[i - 1]:
                transitions += 1

            for s in range(self.samples_per_bit):
                t = bit_start_time + s * dt
                time_points.append(t)
                voltages.append(level)

        transition_density = transitions / (num_bits - 1) if num_bits > 1 else 0.0
        average_voltage = sum(voltages) / len(voltages)

        metadata: Dict[str, object] = {
            "scheme": self.scheme_name,
            "zero_is_positive": self.zero_is_positive,
            "bit_mapping": {
                "0": self.bit_to_voltage("0"),
                "1": self.bit_to_voltage("1"),
            },
            "transitions": transitions,
            "transition_density": transition_density,
            "average_voltage": average_voltage,
            "has_dc_bias": abs(average_voltage) > 1e-6,
        }

        return SignalWaveform(
            bits=bits,
            time_points=time_points,
            voltages=voltages,
            samples_per_bit=self.samples_per_bit,
            bit_duration=self.bit_duration,
            positive_voltage=self.positive_voltage,
            negative_voltage=self.negative_voltage,
            zero_voltage=self.zero_voltage,
            metadata=metadata,
        )

    def decode(self, waveform: SignalWaveform) -> str:
        """
        Decodes a physical SignalWaveform back to binary bits by sampling at bit mid-points.

        Simulates receiver clock recovery and decision slicing at t = (i + 0.5) * Tb.

        :param waveform: Encoded SignalWaveform object.
        :return: Reconstructed binary string.
        """
        if waveform.num_bits == 0:
            return ""

        recovered_bits: List[str] = []
        for i in range(waveform.num_bits):
            _, v_mid = waveform.get_midpoint_sample(i)
            bit = self.voltage_to_bit(v_mid)
            recovered_bits.append(bit)

        return "".join(recovered_bits)

    def calculate_transition_density(self, bits: str) -> float:
        """
        Calculates the ratio of voltage transitions to total possible transitions (N - 1).
        Indicates clock synchronization quality (long constant runs have 0 transition density).

        :param bits: Binary bitstream.
        :return: Float between 0.0 and 1.0.
        """
        self._validate_input(bits)
        if len(bits) <= 1:
            return 0.0
        transitions = sum(1 for i in range(1, len(bits)) if bits[i] != bits[i - 1])
        return transitions / (len(bits) - 1)

    def calculate_dc_bias(self, bits: str) -> float:
        """
        Calculates the theoretical average voltage level (DC component) of a bit sequence.

        :param bits: Binary bitstream.
        :return: Average voltage.
        """
        self._validate_input(bits)
        levels = [self.bit_to_voltage(b) for b in bits]
        return sum(levels) / len(levels)
