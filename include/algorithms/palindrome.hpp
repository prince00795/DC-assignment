#pragma once

#include <string>
#include <vector>
#include <tuple>
#include <sstream>
#include <iomanip>

namespace dc {
namespace algorithms {

struct PalindromeResult {
    std::string substring;
    int start = 0;          // 0-indexed inclusive start position in original string
    int end = 0;            // 0-indexed exclusive end position in original string (start + length)
    int length = 0;         // Total length of palindromic substring
    double center_index = 0.0; // Center position in original string (e.g. 2.0 for 'aba', 1.5 for 'abba')
    bool is_even = false;   // True if length is even, False if odd

    std::string to_string() const {
        std::ostringstream oss;
        oss << "PalindromeResult('" << substring << "', [" << start << ":" << end << "], "
            << "len=" << length << ", center=" << std::fixed << std::setprecision(1) << center_index
            << ", " << (is_even ? "even" : "odd") << ")";
        return oss.str();
    }

    bool operator==(const PalindromeResult& other) const {
        return substring == other.substring && start == other.start &&
               end == other.end && length == other.length && is_even == other.is_even;
    }
};

bool is_palindrome(const std::string& s);

class ManachersAlgorithm {
public:
    explicit ManachersAlgorithm(std::string text);

    PalindromeResult find_longest() const;
    std::vector<PalindromeResult> find_all(int min_length = 1, bool unique_substrings = false) const;
    std::vector<int> get_radius_array() const;
    const std::string& get_transformed() const { return transformed_; }

    static std::string preprocess(const std::string& s);

private:
    std::string text_;
    int n_;
    std::string transformed_;
    std::vector<int> radii_;

    static std::pair<std::string, std::vector<int>> compute_radii(const std::string& s);
};

PalindromeResult find_longest_palindrome(const std::string& text);
std::vector<PalindromeResult> find_all_palindromes(const std::string& text, int min_length = 2);
PalindromeResult naive_longest_palindrome(const std::string& s);

} // namespace algorithms
} // namespace dc
