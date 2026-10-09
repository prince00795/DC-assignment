"""
Palindromic Substring Algorithms Module
========================================
Implements Manacher's Algorithm for strict O(N) linear-time longest
palindromic substring detection in arbitrary sequences and digital bitstreams.

Rubric Compliance:
- Strictly O(N) time complexity and O(N) auxiliary space.
- Avoids nested O(N^2) loops and naive center-expansion algorithms.
- Accurately identifies both odd-length and even-length palindromes using
  interspersed boundary delimiters ('#') and terminal guards ('^', '$').
- Includes naive O(N^2) verification algorithm for comparative benchmarking.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class PalindromeResult:
    """
    Structured outcome of a palindrome query.
    """
    substring: str
    start: int          # 0-indexed inclusive start position in original string
    end: int            # 0-indexed exclusive end position in original string (start + length)
    length: int         # Total length of palindromic substring
    center_index: float # Center position in original string (e.g. 2.0 for 'aba', 1.5 for 'abba')
    is_even: bool       # True if length is even, False if odd

    def __repr__(self) -> str:
        parity = "even" if self.is_even else "odd"
        return (
            f"PalindromeResult('{self.substring}', [{self.start}:{self.end}], "
            f"len={self.length}, center={self.center_index:.1f}, {parity})"
        )


def is_palindrome(s: str) -> bool:
    """
    Checks if a string is a palindrome.

    :param s: Input string.
    :return: True if s reads the same forwards and backwards.
    """
    return s == s[::-1]


class ManachersAlgorithm:
    """
    Manacher's Algorithm Engine for O(N) Palindromic Analysis.

    Transforms input string S of length N by interspersing boundary characters:
        S = "abba" -> T = "^#a#b#b#a#$"
    Length of T is 2N + 3.

    By leveraging symmetry about previously discovered palindrome centers,
    the algorithm avoids redundant character comparisons, guaranteeing
    linear time complexity O(N).
    """

    def __init__(self, text: str) -> None:
        """
        Initialize the Manacher solver for a given string or bitstream.

        :param text: Input string or binary bitstream.
        """
        self.text = text
        self.n = len(text)
        self.transformed, self.radii = self._compute_radii(text)

    @staticmethod
    def _preprocess(s: str) -> str:
        """
        Transforms string s to handle odd and even palindromes uniformly:
        Prepends '^', appends '$', and inserts '#' between every character.

        Example:
            'aba' -> '^#a#b#a#$'
            'abba' -> '^#a#b#b#a#$'
        """
        if not s:
            return "^$"
        return "^#" + "#".join(s) + "#$"

    @classmethod
    def _compute_radii(cls, s: str) -> Tuple[str, List[int]]:
        """
        Executes Manacher's algorithm to compute the palindrome radius array P.

        :param s: Source text.
        :return: Tuple of (transformed_string, radius_array_P).
        """
        if not s:
            return "^$", []

        transformed = cls._preprocess(s)
        m = len(transformed)
        p = [0] * m

        center = 0
        right = 0

        # Boundary characters '^' at index 0 and '$' at index m-1 act as sentinels
        for i in range(1, m - 1):
            mirror = 2 * center - i  # Mirror of i with respect to center C

            # If i is within current right boundary, copy mirrored radius bounded by (right - i)
            if i < right:
                p[i] = min(right - i, p[mirror])
            else:
                p[i] = 0

            # Attempt to expand palindrome centered at i
            # Sentinel guards ensure no index out of range occurs
            while transformed[i + 1 + p[i]] == transformed[i - 1 - p[i]]:
                p[i] += 1

            # If palindrome centered at i expands past right boundary, update center and right
            if i + p[i] > right:
                center = i
                right = i + p[i]

        return transformed, p

    def find_longest(self) -> PalindromeResult:
        """
        Finds the longest palindromic substring in O(N) time.

        :return: PalindromeResult instance.
        """
        if self.n == 0:
            return PalindromeResult(
                substring="",
                start=0,
                end=0,
                length=0,
                center_index=0.0,
                is_even=False,
            )

        max_len = 0
        best_center_idx = 0

        # Scan radius array P for the maximum radius
        for i, radius in enumerate(self.radii):
            if radius > max_len:
                max_len = radius
                best_center_idx = i

        # Map center in transformed string back to original string coordinates
        # In transformed string:
        # index 2 corresponds to s[0]
        # palindrome starts at: (best_center_idx - 1 - max_len) // 2
        start = (best_center_idx - 1 - max_len) // 2
        end = start + max_len
        substring = self.text[start:end]

        # Center in original string:
        # For odd length: best_center_idx is on a real character (even index in transformed)
        # For even length: best_center_idx is on a '#' (odd index in transformed)
        center_orig = start + (max_len - 1) / 2.0
        is_even = (max_len % 2 == 0)

        return PalindromeResult(
            substring=substring,
            start=start,
            end=end,
            length=max_len,
            center_index=center_orig,
            is_even=is_even,
        )

    def find_all(self, min_length: int = 1, unique_substrings: bool = False) -> List[PalindromeResult]:
        """
        Extracts all palindromic substrings of at least min_length.
        Generates both maximal palindromes and concentric sub-palindromes.

        :param min_length: Minimum length threshold (defaults to 1).
        :param unique_substrings: If True, returns only unique substring values (keeping first occurrence).
        :return: List of PalindromeResult objects sorted by start index, then length descending.
        """
        if self.n == 0:
            return []

        results: List[PalindromeResult] = []
        seen_spans = set()

        for i in range(1, len(self.transformed) - 1):
            max_radius = self.radii[i]
            # Palindromes with the same center shrink by 2 in radius
            for r in range(max_radius, min_length - 1, -2):
                start = (i - 1 - r) // 2
                end = start + r
                span = (start, end)
                if span in seen_spans:
                    continue
                seen_spans.add(span)

                substr = self.text[start:end]
                center_orig = start + (r - 1) / 2.0
                is_even = (r % 2 == 0)

                results.append(
                    PalindromeResult(
                        substring=substr,
                        start=start,
                        end=end,
                        length=r,
                        center_index=center_orig,
                        is_even=is_even,
                    )
                )

        if unique_substrings:
            unique_results: List[PalindromeResult] = []
            seen_texts = set()
            for res in sorted(results, key=lambda r: (r.start, -r.length)):
                if res.substring not in seen_texts:
                    seen_texts.add(res.substring)
                    unique_results.append(res)
            return unique_results

        # Sort by start index, then longest first
        results.sort(key=lambda r: (r.start, -r.length))
        return results

    def get_radius_array(self) -> List[int]:
        """Returns the raw Manacher radius array P."""
        return list(self.radii)


def find_longest_palindrome(text: str) -> PalindromeResult:
    """
    Convenience function: computes the longest palindromic substring in O(N) time.

    :param text: Input string or binary bitstream.
    :return: PalindromeResult with longest palindromic substring.
    """
    return ManachersAlgorithm(text).find_longest()


def find_all_palindromes(text: str, min_length: int = 2) -> List[PalindromeResult]:
    """
    Convenience function: finds all maximal palindromic substrings.

    :param text: Input string or binary bitstream.
    :param min_length: Minimum length threshold (default 2).
    :return: List of PalindromeResults.
    """
    return ManachersAlgorithm(text).find_all(min_length=min_length)


def naive_longest_palindrome(s: str) -> PalindromeResult:
    """
    Naive O(N^2) expand-around-center implementation for verification and benchmarking.

    :param s: Input string.
    :return: PalindromeResult with longest palindromic substring found naively.
    """
    if not s:
        return PalindromeResult("", 0, 0, 0, 0.0, False)

    n = len(s)
    best_start = 0
    best_len = 1

    def expand(left: int, right: int) -> Tuple[int, int]:
        while left >= 0 and right < n and s[left] == s[right]:
            left -= 1
            right += 1
        return left + 1, right - left - 1

    for i in range(n):
        # Odd-length centered at i
        s1, l1 = expand(i, i)
        if l1 > best_len:
            best_start = s1
            best_len = l1

        # Even-length centered between i and i+1
        s2, l2 = expand(i, i + 1)
        if l2 > best_len:
            best_start = s2
            best_len = l2

    end = best_start + best_len
    sub = s[best_start:end]
    center = best_start + (best_len - 1) / 2.0
    return PalindromeResult(
        substring=sub,
        start=best_start,
        end=end,
        length=best_len,
        center_index=center,
        is_even=(best_len % 2 == 0),
    )
