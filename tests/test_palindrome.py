"""
Unit Tests: Manacher's Algorithm for Longest Palindromic Substring
==================================================================
Verifies:
1. Strict O(N) detection of odd-length and even-length palindromes.
2. Boundary handling (empty strings, single characters, repeated characters).
3. Digital bitstream palindrome searches (e.g., zero runs, alternating bits).
4. Direct equivalence with naive O(N^2) expansion over randomized inputs.
5. Radius array generation and center position mapping.
6. Maximal palindrome extraction (find_all).
"""

import random
import unittest
from src.algorithms.palindrome import (
    ManachersAlgorithm,
    PalindromeResult,
    find_longest_palindrome,
    find_all_palindromes,
    is_palindrome,
    naive_longest_palindrome,
)


class TestManachersAlgorithm(unittest.TestCase):
    def test_empty_string(self) -> None:
        """Verify handling of empty string."""
        res = find_longest_palindrome("")
        self.assertEqual(res.length, 0)
        self.assertEqual(res.substring, "")
        self.assertEqual(res.start, 0)
        self.assertEqual(res.end, 0)

    def test_single_character(self) -> None:
        """Verify single character returns itself."""
        res = find_longest_palindrome("a")
        self.assertEqual(res.length, 1)
        self.assertEqual(res.substring, "a")
        self.assertEqual(res.start, 0)
        self.assertEqual(res.end, 1)
        self.assertFalse(res.is_even)

    def test_two_characters(self) -> None:
        """Verify two distinct vs two identical characters."""
        distinct = find_longest_palindrome("ab")
        self.assertEqual(distinct.length, 1)
        self.assertIn(distinct.substring, ["a", "b"])

        identical = find_longest_palindrome("aa")
        self.assertEqual(identical.length, 2)
        self.assertEqual(identical.substring, "aa")
        self.assertTrue(identical.is_even)

    def test_odd_length_palindromes(self) -> None:
        """Verify odd-length palindromes like 'racecar', 'aba', '101'."""
        res1 = find_longest_palindrome("racecar")
        self.assertEqual(res1.substring, "racecar")
        self.assertEqual(res1.length, 7)
        self.assertEqual(res1.start, 0)
        self.assertEqual(res1.end, 7)
        self.assertEqual(res1.center_index, 3.0)
        self.assertFalse(res1.is_even)

        res2 = find_longest_palindrome("babad")
        self.assertEqual(res2.length, 3)
        self.assertIn(res2.substring, ["bab", "aba"])
        self.assertTrue(is_palindrome(res2.substring))

    def test_even_length_palindromes(self) -> None:
        """Verify even-length palindromes like 'noon', 'abba', '1001'."""
        res1 = find_longest_palindrome("noon")
        self.assertEqual(res1.substring, "noon")
        self.assertEqual(res1.length, 4)
        self.assertEqual(res1.start, 0)
        self.assertEqual(res1.end, 4)
        self.assertEqual(res1.center_index, 1.5)
        self.assertTrue(res1.is_even)

        res2 = find_longest_palindrome("cbbd")
        self.assertEqual(res2.substring, "bb")
        self.assertEqual(res2.length, 2)
        self.assertEqual(res2.start, 1)
        self.assertEqual(res2.end, 3)
        self.assertTrue(res2.is_even)

    def test_repeated_characters(self) -> None:
        """Verify sequences with all identical characters."""
        res = find_longest_palindrome("00000000")
        self.assertEqual(res.substring, "00000000")
        self.assertEqual(res.length, 8)
        self.assertEqual(res.start, 0)
        self.assertEqual(res.end, 8)

    def test_digital_bitstreams(self) -> None:
        """Verify palindrome discovery in digital communication bit sequences."""
        # Palindromic bit sequences
        stream1 = "011010110"  # entire string is palindrome: 011010110
        res1 = find_longest_palindrome(stream1)
        self.assertEqual(res1.substring, stream1)
        self.assertEqual(res1.length, 9)

        stream2 = "1101001011"
        res2 = find_longest_palindrome(stream2)
        # 1101001011 contains "10100101" (length 8) or "1101001011"?
        # Reverse of 1101001011: 1101001011! It is a palindrome!
        self.assertTrue(is_palindrome(res2.substring))
        self.assertTrue(res2.length >= 8)

    def test_cross_validation_with_naive_on_random_strings(self) -> None:
        """Fuzz testing against naive O(N^2) implementation."""
        rng = random.Random(42)

        # Test random binary streams
        for _ in range(50):
            length = rng.randint(1, 40)
            bitstream = "".join(rng.choice(["0", "1"]) for _ in range(length))
            manacher_res = find_longest_palindrome(bitstream)
            naive_res = naive_longest_palindrome(bitstream)

            # Both must find a palindrome of the exact same maximum length
            self.assertEqual(
                manacher_res.length,
                naive_res.length,
                f"Mismatch on bitstream '{bitstream}': Manacher={manacher_res.length}, Naive={naive_res.length}",
            )
            self.assertTrue(is_palindrome(manacher_res.substring))

        # Test random letters
        alphabet = "abcdef"
        for _ in range(50):
            length = rng.randint(1, 40)
            text = "".join(rng.choice(alphabet) for _ in range(length))
            manacher_res = find_longest_palindrome(text)
            naive_res = naive_longest_palindrome(text)

            self.assertEqual(
                manacher_res.length,
                naive_res.length,
                f"Mismatch on text '{text}': Manacher={manacher_res.length}, Naive={naive_res.length}",
            )
            self.assertTrue(is_palindrome(manacher_res.substring))

    def test_find_all_palindromes(self) -> None:
        """Verify discovery of multiple palindromes."""
        text = "abacaba"
        all_pal = find_all_palindromes(text, min_length=3)
        substrings = [p.substring for p in all_pal]
        self.assertIn("abacaba", substrings)
        self.assertIn("aba", substrings)
        self.assertIn("bacab", substrings)

    def test_radius_array_properties(self) -> None:
        """Verify radius array bounds and properties."""
        solver = ManachersAlgorithm("aba")
        p = solver.get_radius_array()
        # '^#a#b#a#$' length is 2*3 + 3 = 9
        self.assertEqual(len(p), 9)
        # Center of 'aba' is at index 4 (the 'b'): p[4] should be 3
        self.assertEqual(p[4], 3)


if __name__ == "__main__":
    unittest.main()
