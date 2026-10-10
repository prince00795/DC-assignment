"""
Uniform Quantization & Binary Encoding Module
==============================================
Implements Pulse Code Modulation (PCM) uniform quantization:
- Configurable resolution: n bits -> L = 2^n quantization levels.
- Step size calculation: Delta = (V_max - V_min) / 2^n.
- Quantizer types: Mid-rise and Mid-tread decision mapping.
- Binary code assignment:
    * Natural offset binary (e.g. 0 -> '000', L-1 -> '111')
    * Gray coding (adjacent level Hamming distance of 1 to minimize bit errors)
    * Two's complement representation
- Quantization error & noise characterization:
    * Individual sample errors: e[n] = q[n] - x[n]
    * Maximum error bounds: |e| <= Delta / 2 (unclipped)
    * Empirical quantization noise power: P_Q = sum(e^2) / N
    * Theoretical noise power: Delta^2 / 12
    * Empirical and theoretical SQNR (dB): 6.02 * n + 1.76 dB
- Reconstruction (DAC dequantization) from quantization indices and bitstreams.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class QuantizationResult:
    """
    Structured outcome of uniform quantization.
    """
    original_samples: List[float]
    quantized_samples: List[float]
    quantization_indices: List[int]
    binary_codes: List[str]
    bitstream: str
    num_bits: int
    num_levels: int
    step_size: float
    v_min: float
    v_max: float
    coding_scheme: str
    quantization_errors: List[float]
    max_error: float
    clipping_occurred: bool
    clipped_sample_count: int
    empirical_noise_power: float
    theoretical_noise_power: float
    empirical_sqnr_db: float
    theoretical_sqnr_db: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def num_samples(self) -> int:
        """Total number of quantized discrete samples."""
        return len(self.quantized_samples)

    @property
    def total_bits(self) -> int:
        """Total number of bits in the serialized bitstream."""
        return len(self.bitstream)

    def summary(self) -> str:
        """Formatted summary of quantization metrics."""
        lines = [
            f"QuantizationResult [Bits: {self.num_bits}, Levels: {self.num_levels}, Coding: {self.coding_scheme.upper()}]",
            f" - Dynamic Range:             [{self.v_min:+.2f}V, {self.v_max:+.2f}V]",
            f" - Quantization Step Size (Δ): {self.step_size:.4f} V",
            f" - Max Quantization Error:    {self.max_error:.4f} V (Bound: Δ/2 = {self.step_size / 2:.4f} V)",
            f" - Empirical Noise Power:     {self.empirical_noise_power:.4e} V^2",
            f" - Theoretical Noise (Δ²/12): {self.theoretical_noise_power:.4e} V^2",
            f" - Empirical SQNR:            {self.empirical_sqnr_db:.2f} dB",
            f" - Theoretical Full-Scale:    {self.theoretical_sqnr_db:.2f} dB",
            f" - Total Samples:             {self.num_samples} -> Serial Bitstream: {self.total_bits} bits",
            f" - Clipping Overload:         {'YES (' + str(self.clipped_sample_count) + ' samples)' if self.clipping_occurred else 'None'}",
        ]
        return "\n".join(lines)


class UniformQuantizer:
    """
    Uniform Amplitude Quantizer & Binary Codec.
    Converts continuous amplitude samples into discrete PCM levels and binary streams.
    """

    def __init__(
        self,
        num_bits: int = 3,
        v_min: float = -1.0,
        v_max: float = 1.0,
        quantization_type: str = "midrise",
        coding_scheme: str = "natural",
    ) -> None:
        """
        Configure the uniform quantizer.

        :param num_bits: Quantization bit depth n (>= 1). Total levels L = 2^n.
        :param v_min: Lower amplitude boundary.
        :param v_max: Upper amplitude boundary.
        :param quantization_type: 'midrise' or 'midtread'.
        :param coding_scheme: 'natural', 'gray', or 'twos_complement'.
        """
        if num_bits < 1:
            raise ValueError(f"num_bits must be at least 1, got {num_bits}")
        if v_min >= v_max:
            raise ValueError(f"v_min ({v_min}) must be strictly less than v_max ({v_max})")

        coding = coding_scheme.strip().lower()
        if coding not in ("natural", "gray", "twos_complement"):
            raise ValueError(f"Unsupported coding scheme '{coding_scheme}', must be 'natural', 'gray', or 'twos_complement'")

        q_type = quantization_type.strip().lower()
        if q_type not in ("midrise", "midtread"):
            raise ValueError(f"Unsupported quantization type '{quantization_type}', must be 'midrise' or 'midtread'")

        self.num_bits = num_bits
        self.num_levels = 1 << num_bits  # 2^n
        self.v_min = float(v_min)
        self.v_max = float(v_max)
        self.quantization_type = q_type
        self.coding_scheme = coding

        # Step size Delta = (V_max - V_min) / 2^n
        self.step_size = (self.v_max - self.v_min) / float(self.num_levels)

        # Precompute reconstruction levels
        self.reconstruction_levels = [
            self.v_min + (k + 0.5) * self.step_size for k in range(self.num_levels)
        ]

        # Precompute index <-> binary codeword mapping
        self._index_to_code: Dict[int, str] = {}
        self._code_to_index: Dict[str, int] = {}
        self._build_code_tables()

    def _build_code_tables(self) -> None:
        """Builds lookup tables for index to binary code mapping."""
        n = self.num_bits
        for k in range(self.num_levels):
            if self.coding_scheme == "natural":
                code = format(k, f"0{n}b")
            elif self.coding_scheme == "gray":
                # Gray code: G = k ^ (k >> 1)
                gray_val = k ^ (k >> 1)
                code = format(gray_val, f"0{n}b")
            elif self.coding_scheme == "twos_complement":
                # Shifted by L/2 to represent signed values
                signed_val = k - (self.num_levels // 2)
                if signed_val < 0:
                    code = format((1 << n) + signed_val, f"0{n}b")
                else:
                    code = format(signed_val, f"0{n}b")
            else:
                code = format(k, f"0{n}b")

            self._index_to_code[k] = code
            self._code_to_index[code] = k

    @classmethod
    def from_signal(
        cls,
        samples: Sequence[float],
        num_bits: int = 3,
        headroom_ratio: float = 0.05,
        coding_scheme: str = "natural",
    ) -> UniformQuantizer:
        """
        Factory to automatically scale the dynamic range to encompass the input signal
        with a configurable percentage headroom.

        :param samples: Sequence of sample values.
        :param num_bits: Bit depth.
        :param headroom_ratio: Percentage margin added to peak amplitude (default 5%).
        :param coding_scheme: Binary mapping scheme.
        :return: Configured UniformQuantizer instance.
        """
        if not samples:
            raise ValueError("Cannot configure quantizer from empty samples sequence.")

        peak = max(abs(min(samples)), abs(max(samples)))
        if peak == 0.0:
            peak = 1.0

        limit = peak * (1.0 + headroom_ratio)
        return cls(
            num_bits=num_bits,
            v_min=-limit,
            v_max=limit,
            coding_scheme=coding_scheme,
        )

    def quantize_sample(self, x: float) -> Tuple[float, int, str]:
        """
        Quantizes an individual scalar sample value.

        :param x: Sample voltage amplitude.
        :return: Tuple of (quantized_voltage, level_index, binary_code).
        """
        # Determine level index
        if x <= self.v_min:
            idx = 0
        elif x >= self.v_max:
            idx = self.num_levels - 1
        else:
            idx = int((x - self.v_min) / self.step_size)
            if idx >= self.num_levels:
                idx = self.num_levels - 1

        q_val = self.reconstruction_levels[idx]
        code = self._index_to_code[idx]
        return q_val, idx, code

    def quantize(self, samples: Sequence[float]) -> QuantizationResult:
        """
        Performs uniform quantization on a sequence of sampled amplitudes.

        :param samples: Sequence of floating-point analog samples.
        :return: QuantizationResult instance.
        """
        if not samples:
            raise ValueError("Input samples sequence cannot be empty.")

        quantized_vals: List[float] = []
        indices: List[int] = []
        codes: List[str] = []
        errors: List[float] = []
        clipped_count = 0

        for x in samples:
            if x < self.v_min or x > self.v_max:
                clipped_count += 1

            q_val, idx, code = self.quantize_sample(x)
            quantized_vals.append(q_val)
            indices.append(idx)
            codes.append(code)
            errors.append(q_val - x)

        bitstream = "".join(codes)
        max_error = max(abs(e) for e in errors)
        clipping_occurred = clipped_count > 0

        # Empirical noise power: sum(e^2) / N
        empirical_noise = sum(e ** 2 for e in errors) / len(errors)

        # Theoretical noise power: Delta^2 / 12
        theoretical_noise = (self.step_size ** 2) / 12.0

        # Signal power for empirical SQNR
        sig_power = sum(x ** 2 for x in samples) / len(samples)
        if empirical_noise > 1e-12 and sig_power > 1e-12:
            empirical_sqnr = 10.0 * math.log10(sig_power / empirical_noise)
        elif empirical_noise <= 1e-12:
            empirical_sqnr = 120.0
        else:
            empirical_sqnr = 0.0

        # Theoretical sinusoidal full-scale rule of thumb: 6.02 * n + 1.76 dB
        theoretical_sqnr = 6.02 * self.num_bits + 1.76

        return QuantizationResult(
            original_samples=list(samples),
            quantized_samples=quantized_vals,
            quantization_indices=indices,
            binary_codes=codes,
            bitstream=bitstream,
            num_bits=self.num_bits,
            num_levels=self.num_levels,
            step_size=self.step_size,
            v_min=self.v_min,
            v_max=self.v_max,
            coding_scheme=self.coding_scheme,
            quantization_errors=errors,
            max_error=max_error,
            clipping_occurred=clipping_occurred,
            clipped_sample_count=clipped_count,
            empirical_noise_power=empirical_noise,
            theoretical_noise_power=theoretical_noise,
            empirical_sqnr_db=empirical_sqnr,
            theoretical_sqnr_db=theoretical_sqnr,
        )

    def dequantize(self, indices: Sequence[int]) -> List[float]:
        """
        Converts quantization level indices back into discrete voltage levels.

        :param indices: Sequence of integer indices [0, L - 1].
        :return: Reconstructed voltage levels.
        """
        reconstructed: List[float] = []
        for idx in indices:
            if idx < 0 or idx >= self.num_levels:
                raise IndexError(f"Quantization index {idx} out of range [0, {self.num_levels - 1}]")
            reconstructed.append(self.reconstruction_levels[idx])
        return reconstructed

    def decode_bitstream(self, bitstream: str) -> List[float]:
        """
        Dequantizes a serialized PCM bitstream back to discrete voltage levels.
        Simulates the digital-to-analog converter (DAC) reconstruction stage.

        :param bitstream: String of '0' and '1' characters.
        :return: List of reconstructed voltage levels.
        """
        n = self.num_bits
        if len(bitstream) % n != 0:
            raise ValueError(
                f"Bitstream length ({len(bitstream)}) is not an exact multiple of bit depth ({n})."
            )

        indices: List[int] = []
        for i in range(0, len(bitstream), n):
            chunk = bitstream[i : i + n]
            if chunk not in self._code_to_index:
                raise ValueError(f"Invalid codeword '{chunk}' encountered during bitstream decoding.")
            indices.append(self._code_to_index[chunk])

        return self.dequantize(indices)
