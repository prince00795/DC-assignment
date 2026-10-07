"""
Digital Data Generator Module
=============================
Generates binary digital sequences:
- Uniform random bitstreams.
- Pattern-injected bitstreams containing guaranteed runs of consecutive zeros
  (e.g., 4 zeros for HDB3, 8 zeros for B8ZS).
- Arbitrary pattern injection and zero-run analysis for scrambling testbeds.
"""

from __future__ import annotations
import random
from typing import List, Optional, Tuple


class DataGenerator:
    """Generates digital bitstreams for transmission, line coding, and scrambling."""

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

        zero_block = ["0"] * zero_run_length
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

    def generate_b8zs_stream(self, length: int, num_injections: int = 1) -> str:
        """
        Convenience generator for B8ZS scrambling testing.
        Guarantees runs of 8 consecutive zeros ('00000000').

        :param length: Total length of the bitstream (must be >= 8 * num_injections).
        :param num_injections: Number of 8-zero sequences to embed.
        :return: Binary bitstream with embedded 8-zero sequences.
        """
        return self.generate_with_fixed_zeros(
            length=length,
            zero_run_length=8,
            num_injections=num_injections,
        )

    def generate_hdb3_stream(self, length: int, num_injections: int = 1) -> str:
        """
        Convenience generator for HDB3 scrambling testing.
        Guarantees runs of 4 consecutive zeros ('0000').

        :param length: Total length of the bitstream (must be >= 4 * num_injections).
        :param num_injections: Number of 4-zero sequences to embed.
        :return: Binary bitstream with embedded 4-zero sequences.
        """
        return self.generate_with_fixed_zeros(
            length=length,
            zero_run_length=4,
            num_injections=num_injections,
        )

    def inject_pattern(
        self,
        base_stream: str,
        pattern: str,
        position: Optional[int] = None,
        overwrite: bool = True,
    ) -> str:
        """
        Injects a specific binary pattern into an existing bitstream.

        :param base_stream: Base binary string.
        :param pattern: Binary pattern to inject (e.g., '00000000' or '101010').
        :param position: 0-based insertion/overwrite index. If None, picked uniformly at random.
        :param overwrite: If True, overwrites bits starting at position (length preserved).
                          If False, inserts pattern at position (length increases).
        :return: Resulting binary bitstream.
        """
        if not self.validate_stream(base_stream):
            raise ValueError(f"Base stream must be a non-empty binary string, got '{base_stream}'")
        if not self.validate_stream(pattern):
            raise ValueError(f"Pattern must be a non-empty binary string, got '{pattern}'")

        if overwrite:
            if len(pattern) > len(base_stream):
                raise ValueError(
                    f"Pattern length ({len(pattern)}) exceeds base stream length ({len(base_stream)}) for overwrite."
                )
            max_pos = len(base_stream) - len(pattern)
            if position is None:
                pos = self._rng.randint(0, max_pos)
            else:
                if position < 0 or position > max_pos:
                    raise IndexError(f"Position {position} out of valid range [0, {max_pos}]")
                pos = position
            return base_stream[:pos] + pattern + base_stream[pos + len(pattern):]
        else:
            max_pos = len(base_stream)
            if position is None:
                pos = self._rng.randint(0, max_pos)
            else:
                if position < 0 or position > max_pos:
                    raise IndexError(f"Position {position} out of valid range [0, {max_pos}]")
                pos = position
            return base_stream[:pos] + pattern + base_stream[pos:]

    @staticmethod
    def validate_stream(bitstream: str) -> bool:
        """
        Validates that a string is a non-empty binary bitstream containing only '0' and '1'.

        :param bitstream: Input string to validate.
        :return: True if valid, False otherwise.
        """
        if not bitstream:
            return False
        return all(bit in ("0", "1") for bit in bitstream)

    @staticmethod
    def find_zero_runs(bitstream: str) -> List[Tuple[int, int]]:
        """
        Scans a bitstream and returns all contiguous runs of zeros.

        :param bitstream: Binary string to inspect.
        :return: List of tuples (start_index, run_length).
        """
        runs: List[Tuple[int, int]] = []
        in_run = False
        start_idx = 0
        current_len = 0

        for idx, bit in enumerate(bitstream):
            if bit == "0":
                if not in_run:
                    in_run = True
                    start_idx = idx
                    current_len = 1
                else:
                    current_len += 1
            else:
                if in_run:
                    runs.append((start_idx, current_len))
                    in_run = False
                    current_len = 0

        if in_run:
            runs.append((start_idx, current_len))

        return runs

    @staticmethod
    def max_consecutive_zeros(bitstream: str) -> int:
        """
        Calculates the maximum number of consecutive zeros in a bitstream.

        :param bitstream: Binary string to inspect.
        :return: Length of the longest run of consecutive zeros (0 if no zeros).
        """
        runs = DataGenerator.find_zero_runs(bitstream)
        if not runs:
            return 0
        return max(run_len for _, run_len in runs)
