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


class NRZIEncoder(LineEncoder):
    """
    Non-Return-to-Zero-Invert (NRZ-I) Line Encoder & Decoder.

    In NRZ-I, the presence or absence of a signal transition (inversion between +V and -V)
    at the start of a bit interval represents the binary bit value:
    - Standard Telecom / USB Convention (transition_on_one=True):
        * Bit '1' -> Transition (voltage inverts: +V -> -V or -V -> +V)
        * Bit '0' -> No Transition (voltage maintains prior level)
    - Inverted Convention (transition_on_one=False):
        * Bit '0' -> Transition (voltage inverts)
        * Bit '1' -> No Transition (voltage maintains prior level)

    Differential Line Coding Highlights:
    - Eliminates polarity inversion ambiguity in physical twisted-pair or coaxial lines.
    - Differential transition tracking: tracks every edge occurrence and density.
    - Mid-point receiver probing compares adjacent bit levels to reconstruct bitstream.
    """

    def __init__(
        self,
        samples_per_bit: int = 100,
        bit_duration: float = 1.0,
        positive_voltage: float = 1.0,
        negative_voltage: float = -1.0,
        zero_voltage: float = 0.0,
        transition_on_one: bool = True,
        initial_voltage: Optional[float] = None,
    ) -> None:
        """
        Initialize the NRZ-I Encoder.

        :param samples_per_bit: Discrete time samples per bit interval.
        :param bit_duration: Bit duration Tb in seconds.
        :param positive_voltage: High voltage level +V (default: +1.0V).
        :param negative_voltage: Low voltage level -V (default: -1.0V).
        :param zero_voltage: Reference ground level (default: 0.0V).
        :param transition_on_one: If True, '1' triggers an inversion; if False, '0' triggers an inversion.
        :param initial_voltage: Reference voltage prior to transmission (defaults to positive_voltage).
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
        self.transition_on_one = transition_on_one
        self.default_initial_voltage = (
            initial_voltage if initial_voltage is not None else positive_voltage
        )

    @property
    def scheme_name(self) -> str:
        """Name of the line coding scheme."""
        return "NRZ-I"

    def invert_voltage(self, voltage: float) -> float:
        """
        Inverts a voltage between the positive and negative levels.

        :param voltage: Current voltage level.
        :return: Opposite voltage level.
        """
        threshold = (self.positive_voltage + self.negative_voltage) / 2.0
        return self.negative_voltage if voltage >= threshold else self.positive_voltage

    def encode(self, bits: str, initial_voltage: Optional[float] = None) -> SignalWaveform:
        """
        Encodes a binary bitstream into a physical SignalWaveform using differential transitions.

        :param bits: Binary string (e.g., "101100").
        :param initial_voltage: Optional starting level override.
        :return: SignalWaveform with discrete time points and differential voltage levels.
        """
        self._validate_input(bits)

        init_v = initial_voltage if initial_voltage is not None else self.default_initial_voltage
        current_v = init_v

        time_points: List[float] = []
        voltages: List[float] = []
        bit_levels: List[float] = []
        transition_indices: List[int] = []
        dt = self.bit_duration / self.samples_per_bit
        num_bits = len(bits)

        transitions = 0
        for i, bit in enumerate(bits):
            trigger = (bit == "1") if self.transition_on_one else (bit == "0")
            if trigger:
                current_v = self.invert_voltage(current_v)
                transitions += 1
                transition_indices.append(i)

            bit_levels.append(current_v)
            bit_start_time = i * self.bit_duration

            for s in range(self.samples_per_bit):
                t = bit_start_time + s * dt
                time_points.append(t)
                voltages.append(current_v)

        transition_density = transitions / num_bits if num_bits > 0 else 0.0
        average_voltage = sum(voltages) / len(voltages)

        metadata: Dict[str, object] = {
            "scheme": self.scheme_name,
            "transition_on_one": self.transition_on_one,
            "initial_voltage": init_v,
            "transitions": transitions,
            "transition_indices": transition_indices,
            "transition_density": transition_density,
            "average_voltage": average_voltage,
            "has_dc_bias": abs(average_voltage) > 1e-6,
            "bit_levels": bit_levels,
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

    def decode(self, waveform: SignalWaveform, initial_voltage: Optional[float] = None) -> str:
        """
        Decodes a physical SignalWaveform back to binary bits using differential transition detection.

        Samples mid-points and identifies whether the voltage crossed the decision threshold
        relative to the previous bit's level.

        :param waveform: Encoded SignalWaveform object.
        :param initial_voltage: Starting reference voltage level (defaults to waveform metadata or default).
        :return: Reconstructed binary string.
        """
        if waveform.num_bits == 0:
            return ""

        init_v = initial_voltage
        if init_v is None:
            init_v = waveform.metadata.get("initial_voltage", self.default_initial_voltage)

        threshold = (self.positive_voltage + self.negative_voltage) / 2.0
        prev_is_high = (init_v >= threshold)

        recovered_bits: List[str] = []
        for i in range(waveform.num_bits):
            _, v_mid = waveform.get_midpoint_sample(i)
            curr_is_high = (v_mid >= threshold)

            transition_occurred = (curr_is_high != prev_is_high)
            if self.transition_on_one:
                bit = "1" if transition_occurred else "0"
            else:
                bit = "0" if transition_occurred else "1"

            recovered_bits.append(bit)
            prev_is_high = curr_is_high

        return "".join(recovered_bits)

    def calculate_transition_density(self, bits: str) -> float:
        """
        Calculates the theoretical transition density for NRZ-I on a given bitstream.
        In NRZ-I, transition density is determined by the frequency of trigger bits.

        :param bits: Binary bitstream.
        :return: Float between 0.0 and 1.0.
        """
        self._validate_input(bits)
        if not bits:
            return 0.0
        trigger_char = "1" if self.transition_on_one else "0"
        transitions = bits.count(trigger_char)
        return transitions / len(bits)

    def calculate_dc_bias(self, bits: str, initial_voltage: Optional[float] = None) -> float:
        """
        Calculates the average DC voltage of an NRZ-I encoded bitstream.

        :param bits: Binary bitstream.
        :param initial_voltage: Starting reference level.
        :return: Average voltage.
        """
        self._validate_input(bits)
        wf = self.encode(bits, initial_voltage=initial_voltage)
        return wf.metadata["average_voltage"]

