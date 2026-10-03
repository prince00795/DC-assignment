#include "generator/data_generator.hpp"
#include <stdexcept>
#include <algorithm>

namespace dc {
namespace generator {

DataGenerator::DataGenerator(std::optional<uint64_t> seed) {
    set_seed(seed);
}

void DataGenerator::set_seed(std::optional<uint64_t> seed) {
    if (seed.has_value()) {
        rng_.seed(seed.value());
    } else {
        std::random_device rd;
        rng_.seed(rd());
    }
}

std::string DataGenerator::generate_random(int length) {
    if (length <= 0) {
        throw std::invalid_argument("Stream length must be positive, got " + std::to_string(length));
    }
    std::uniform_int_distribution<int> dist(0, 1);
    std::string s;
    s.reserve(length);
    for (int i = 0; i < length; ++i) {
        s.push_back(dist(rng_) ? '1' : '0');
    }
    return s;
}

std::string DataGenerator::generate_with_fixed_zeros(int length, int zero_run_length, int num_injections) {
    if (length <= 0) {
        throw std::invalid_argument("Stream length must be positive, got " + std::to_string(length));
    }
    if (zero_run_length <= 0) {
        throw std::invalid_argument("zero_run_length must be positive, got " + std::to_string(zero_run_length));
    }
    if (zero_run_length * num_injections > length) {
        throw std::invalid_argument(
            "Requested " + std::to_string(num_injections) + " runs of length " +
            std::to_string(zero_run_length) + " which exceeds total stream length " + std::to_string(length)
        );
    }

    std::string zero_block(zero_run_length, '0');
    int total_zero_bits = zero_run_length * num_injections;
    int remaining_bits = length - total_zero_bits;

    std::vector<int> gaps(num_injections + 1, 0);
    std::uniform_int_distribution<int> gap_dist(0, num_injections);
    for (int i = 0; i < remaining_bits; ++i) {
        gaps[gap_dist(rng_)]++;
    }

    std::uniform_int_distribution<int> bit_dist(0, 1);
    std::string result;
    result.reserve(length);

    for (int i = 0; i < num_injections; ++i) {
        for (int g = 0; g < gaps[i]; ++g) {
            result.push_back(bit_dist(rng_) ? '1' : '0');
        }
        result.append(zero_block);
    }

    for (int g = 0; g < gaps[num_injections]; ++g) {
        result.push_back(bit_dist(rng_) ? '1' : '0');
    }

    return result;
}

std::string DataGenerator::generate_b8zs_stream(int length, int num_injections) {
    return generate_with_fixed_zeros(length, 8, num_injections);
}

std::string DataGenerator::generate_hdb3_stream(int length, int num_injections) {
    return generate_with_fixed_zeros(length, 4, num_injections);
}

std::string DataGenerator::inject_pattern(
    const std::string& base_stream,
    const std::string& pattern,
    std::optional<int> position,
    bool overwrite
) {
    if (!validate_stream(base_stream)) {
        throw std::invalid_argument("Base stream must be a non-empty binary string, got '" + base_stream + "'");
    }
    if (!validate_stream(pattern)) {
        throw std::invalid_argument("Pattern must be a non-empty binary string, got '" + pattern + "'");
    }

    int base_len = static_cast<int>(base_stream.size());
    int pat_len = static_cast<int>(pattern.size());

    if (overwrite) {
        if (pat_len > base_len) {
            throw std::invalid_argument(
                "Pattern length (" + std::to_string(pat_len) + ") exceeds base stream length (" +
                std::to_string(base_len) + ") for overwrite."
            );
        }
        int max_pos = base_len - pat_len;
        int pos = 0;
        if (!position.has_value()) {
            std::uniform_int_distribution<int> dist(0, max_pos);
            pos = dist(rng_);
        } else {
            pos = position.value();
            if (pos < 0 || pos > max_pos) {
                throw std::out_of_range("Position " + std::to_string(pos) + " out of valid range [0, " + std::to_string(max_pos) + "]");
            }
        }
        std::string res = base_stream;
        res.replace(pos, pat_len, pattern);
        return res;
    } else {
        int max_pos = base_len;
        int pos = 0;
        if (!position.has_value()) {
            std::uniform_int_distribution<int> dist(0, max_pos);
            pos = dist(rng_);
        } else {
            pos = position.value();
            if (pos < 0 || pos > max_pos) {
                throw std::out_of_range("Position " + std::to_string(pos) + " out of valid range [0, " + std::to_string(max_pos) + "]");
            }
        }
        std::string res = base_stream;
        res.insert(pos, pattern);
        return res;
    }
}

bool DataGenerator::validate_stream(const std::string& bitstream) {
    if (bitstream.empty()) return false;
    for (char c : bitstream) {
        if (c != '0' && c != '1') return false;
    }
    return true;
}

std::vector<std::pair<int, int>> DataGenerator::find_zero_runs(const std::string& bitstream) {
    std::vector<std::pair<int, int>> runs;
    bool in_run = false;
    int start_idx = 0;
    int current_len = 0;

    for (size_t idx = 0; idx < bitstream.size(); ++idx) {
        if (bitstream[idx] == '0') {
            if (!in_run) {
                in_run = true;
                start_idx = static_cast<int>(idx);
                current_len = 1;
            } else {
                current_len++;
            }
        } else {
            if (in_run) {
                runs.emplace_back(start_idx, current_len);
                in_run = false;
                current_len = 0;
            }
        }
    }

    if (in_run) {
        runs.emplace_back(start_idx, current_len);
    }

    return runs;
}

int DataGenerator::max_consecutive_zeros(const std::string& bitstream) {
    auto runs = find_zero_runs(bitstream);
    if (runs.empty()) return 0;
    int max_len = 0;
    for (const auto& r : runs) {
        if (r.second > max_len) max_len = r.second;
    }
    return max_len;
}

} // namespace generator
} // namespace dc
