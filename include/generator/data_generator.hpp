#pragma once

#include <string>
#include <vector>
#include <random>
#include <optional>
#include <utility>

namespace dc {
namespace generator {

class DataGenerator {
public:
    explicit DataGenerator(std::optional<uint64_t> seed = std::nullopt);

    void set_seed(std::optional<uint64_t> seed);

    std::string generate_random(int length);
    std::string generate_with_fixed_zeros(int length, int zero_run_length = 8, int num_injections = 1);
    std::string generate_b8zs_stream(int length, int num_injections = 1);
    std::string generate_hdb3_stream(int length, int num_injections = 1);

    std::string inject_pattern(
        const std::string& base_stream,
        const std::string& pattern,
        std::optional<int> position = std::nullopt,
        bool overwrite = true
    );

    static bool validate_stream(const std::string& bitstream);
    static std::vector<std::pair<int, int>> find_zero_runs(const std::string& bitstream);
    static int max_consecutive_zeros(const std::string& bitstream);

private:
    std::mt19937_64 rng_;
};

} // namespace generator
} // namespace dc
