"""
Digital Data Generator Module
=============================
Generates binary digital sequences:
- Uniform random bitstreams.
- Bitstreams containing injected consecutive zero runs (e.g., 4 or 8 zeros)
  for testing scrambling schemes such as HDB3 and B8ZS.
"""

from __future__ import annotations
import random
from typing import Optional


class DataGenerator:
    """Generates digital bitstreams for transmission and line coding."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """
        Initialize the generator.

        :param seed: Optional integer seed for reproducible random generation.
        """
        self._rng = random.Random(seed)

    def set_seed(self, seed: Optional[int]) -> None:
        """Reset the random seed."""
        self._rng = random.Random(seed)

    def generate_random(self, length: int) -> str:
        """
        Generates a completely random binary stream of the specified length.

        :param length: Total number of bits to generate (must be >= 1).
        :return: String of '0' and '1' characters.
        """
        if length <= 0:
            raise ValueError(f"Stream length must be positive, got {length}")

        bits = [self._rng.choice(["0", "1"]) for _ in range(length)]
        return "".join(bits)

    def generate_with_fixed_zeros(
        self,
        length: int,
        zero_run_length: int = 8,
        num_injections: int = 1,
    ) -> str:
        """
        Generates a random bitstream with guaranteed runs of consecutive zeros.
        Typically 8 zeros for B8ZS or 4 zeros for HDB3.

        :param length: Total length of the generated bitstream.
        :param zero_run_length: Length of consecutive zeros (e.g., 4 or 8).
        :param num_injections: Number of distinct zero-run blocks to inject.
        :return: Binary string with embedded zero blocks.
        """
        if length <= 0:
            raise ValueError(f"Stream length must be positive, got {length}")
        if zero_run_length <= 0:
            raise ValueError(f"zero_run_length must be positive, got {zero_run_length}")
        if zero_run_length * num_injections > length:
            raise ValueError(
                f"Requested {num_injections} runs of length {zero_run_length} "
                f"which exceeds total stream length {length}."
            )

        # Start with a random bitstream
        stream = list(self.generate_random(length))
        zero_block = ["0"] * zero_run_length

        # Find non-overlapping insertion positions
        # Space available for non-zero gaps:
        total_zero_bits = zero_run_length * num_injections
        remaining_bits = length - total_zero_bits

        # Generate random gap partition
        gaps = [0] * (num_injections + 1)
        for _ in range(remaining_bits):
            idx = self._rng.randint(0, num_injections)
            gaps[idx] += 1

        # Reconstruct stream using partitioned gaps and zero blocks
        result: list[str] = []
        for i in range(num_injections):
            # Fill gap with random bits
            for _ in range(gaps[i]):
                result.append(self._rng.choice(["0", "1"]))
            # Inject zero block
            result.extend(zero_block)

        # Final trailing gap
        for _ in range(gaps[-1]):
            result.append(self._rng.choice(["0", "1"]))

        return "".join(result)

    @staticmethod
    def validate_stream(bitstream: str) -> bool:
        """
        Validates that a string is a valid binary bitstream containing only '0' and '1'.

        :param bitstream: Input string to validate.
        :return: True if valid, False otherwise.
        """
        if not bitstream:
            return False
        return all(bit in ("0", "1") for bit in bitstream)
