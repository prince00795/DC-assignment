#include "algorithms/palindrome.hpp"
#include <algorithm>
#include <unordered_set>

namespace dc {
namespace algorithms {

bool is_palindrome(const std::string& s) {
    if (s.empty()) return true;
    size_t i = 0, j = s.size() - 1;
    while (i < j) {
        if (s[i] != s[j]) return false;
        ++i;
        --j;
    }
    return true;
}

std::string ManachersAlgorithm::preprocess(const std::string& s) {
    if (s.empty()) return "^$";
    std::string res;
    res.reserve(s.size() * 2 + 3);
    res.push_back('^');
    res.push_back('#');
    for (char c : s) {
        res.push_back(c);
        res.push_back('#');
    }
    res.push_back('$');
    return res;
}

std::pair<std::string, std::vector<int>> ManachersAlgorithm::compute_radii(const std::string& s) {
    if (s.empty()) {
        return {"^$", {}};
    }
    std::string transformed = preprocess(s);
    int m = static_cast<int>(transformed.size());
    std::vector<int> p(m, 0);

    int center = 0;
    int right = 0;

    for (int i = 1; i < m - 1; ++i) {
        int mirror = 2 * center - i;

        if (i < right) {
            p[i] = std::min(right - i, p[mirror]);
        } else {
            p[i] = 0;
        }

        while (transformed[i + 1 + p[i]] == transformed[i - 1 - p[i]]) {
            p[i]++;
        }

        if (i + p[i] > right) {
            center = i;
            right = i + p[i];
        }
    }

    return {transformed, p};
}

ManachersAlgorithm::ManachersAlgorithm(std::string text)
    : text_(std::move(text)), n_(static_cast<int>(text_.size())) {
    auto [t, r] = compute_radii(text_);
    transformed_ = std::move(t);
    radii_ = std::move(r);
}

PalindromeResult ManachersAlgorithm::find_longest() const {
    if (n_ == 0) {
        return PalindromeResult{"", 0, 0, 0, 0.0, false};
    }

    int max_len = 0;
    int best_center_idx = 0;

    for (size_t i = 0; i < radii_.size(); ++i) {
        if (radii_[i] > max_len) {
            max_len = radii_[i];
            best_center_idx = static_cast<int>(i);
        }
    }

    int start = (best_center_idx - 1 - max_len) / 2;
    int end = start + max_len;
    std::string substring = text_.substr(start, max_len);
    double center_orig = start + (max_len - 1) / 2.0;
    bool is_even = (max_len % 2 == 0);

    return PalindromeResult{substring, start, end, max_len, center_orig, is_even};
}

std::vector<PalindromeResult> ManachersAlgorithm::find_all(int min_length, bool unique_substrings) const {
    if (n_ == 0) return {};

    std::vector<PalindromeResult> results;
    struct SpanHash {
        size_t operator()(const std::pair<int, int>& p) const {
            return std::hash<int>()(p.first) ^ (std::hash<int>()(p.second) << 16);
        }
    };
    std::unordered_set<std::pair<int, int>, SpanHash> seen_spans;

    int m = static_cast<int>(transformed_.size());
    for (int i = 1; i < m - 1; ++i) {
        int max_radius = radii_[i];
        for (int r = max_radius; r >= min_length; r -= 2) {
            int start = (i - 1 - r) / 2;
            int end = start + r;
            std::pair<int, int> span = {start, end};
            if (seen_spans.find(span) != seen_spans.end()) {
                continue;
            }
            seen_spans.insert(span);

            std::string substr = text_.substr(start, r);
            double center_orig = start + (r - 1) / 2.0;
            bool is_even = (r % 2 == 0);

            results.push_back(PalindromeResult{substr, start, end, r, center_orig, is_even});
        }
    }

    // Sort by start index ascending, then length descending
    std::sort(results.begin(), results.end(), [](const PalindromeResult& a, const PalindromeResult& b) {
        if (a.start != b.start) return a.start < b.start;
        return a.length > b.length;
    });

    if (unique_substrings) {
        std::vector<PalindromeResult> unique_results;
        std::unordered_set<std::string> seen_texts;
        for (const auto& res : results) {
            if (seen_texts.find(res.substring) == seen_texts.end()) {
                seen_texts.insert(res.substring);
                unique_results.push_back(res);
            }
        }
        return unique_results;
    }

    return results;
}

std::vector<int> ManachersAlgorithm::get_radius_array() const {
    return radii_;
}

PalindromeResult find_longest_palindrome(const std::string& text) {
    return ManachersAlgorithm(text).find_longest();
}

std::vector<PalindromeResult> find_all_palindromes(const std::string& text, int min_length) {
    return ManachersAlgorithm(text).find_all(min_length);
}

PalindromeResult naive_longest_palindrome(const std::string& s) {
    if (s.empty()) {
        return PalindromeResult{"", 0, 0, 0, 0.0, false};
    }
    int n = static_cast<int>(s.size());
    int best_start = 0;
    int best_len = 1;

    auto expand = [&](int left, int right) -> std::pair<int, int> {
        while (left >= 0 && right < n && s[left] == s[right]) {
            --left;
            ++right;
        }
        return {left + 1, right - left - 1};
    };

    for (int i = 0; i < n; ++i) {
        auto [s1, l1] = expand(i, i);
        if (l1 > best_len) {
            best_start = s1;
            best_len = l1;
        }
        auto [s2, l2] = expand(i, i + 1);
        if (l2 > best_len) {
            best_start = s2;
            best_len = l2;
        }
    }

    int end = best_start + best_len;
    std::string sub = s.substr(best_start, best_len);
    double center = best_start + (best_len - 1) / 2.0;
    return PalindromeResult{sub, best_start, end, best_len, center, (best_len % 2 == 0)};
}

} // namespace algorithms
} // namespace dc
