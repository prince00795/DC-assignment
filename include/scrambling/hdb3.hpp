#pragma once

#include "line_coding/base.hpp"
#include <string>
#include <vector>
#include <optional>

namespace dc {
namespace scrambling {

struct HDB3SubstitutionRecord {
    int start_index = 0;
    int length = 4;
    std::string rule_applied;
    double previous_polarity = 0.0;
    int pulses_since_last = 0;
    std::vector<double> substituted_levels;
    std::vector<int> violation_indices;
    std::vector<int> bipolar_indices;
};

class HDB3Scrambler {
public:
    explicit HDB3Scrambler(
        double positive_voltage = 1.0,
        double negative_voltage = -1.0,
        double zero_voltage = 0.0,
        int samples_per_bit = 100,
        double bit_duration = 1.0
    );

    std::pair<std::vector<double>, std::vector<HDB3SubstitutionRecord>> scramble(
        const std::string& bits,
        std::optional<double> initial_polarity = std::nullopt
    );

    std::string descramble(const std::vector<double>& pulses);

    line_coding::SignalWaveform encode(
        const std::string& bits,
        std::optional<double> initial_polarity = std::nullopt
    );

    std::string decode(const line_coding::SignalWaveform& waveform);

private:
    double positive_voltage_;
    double negative_voltage_;
    double zero_voltage_;
    int samples_per_bit_;
    double bit_duration_;
};

} // namespace scrambling
} // namespace dc
