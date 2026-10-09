#include "scrambling/b8zs.hpp"
#include <cmath>
#include <stdexcept>

namespace dc {
namespace scrambling {

B8ZSScrambler::B8ZSScrambler(
    double positive_voltage,
    double negative_voltage,
    double zero_voltage,
    int samples_per_bit,
    double bit_duration
) : positive_voltage_(positive_voltage),
    negative_voltage_(negative_voltage),
    zero_voltage_(zero_voltage),
    samples_per_bit_(samples_per_bit),
    bit_duration_(bit_duration) {}

std::pair<std::vector<double>, std::vector<B8ZSSubstitutionRecord>> B8ZSScrambler::scramble(
    const std::string& bits,
    std::optional<double> initial_polarity
) {
    if (bits.empty()) {
        return {{}, {}};
    }
    for (char c : bits) {
        if (c != '0' && c != '1') {
            throw std::invalid_argument(std::string("Non-binary character: ") + c);
        }
    }

    double last_polarity = initial_polarity.value_or(negative_voltage_);
    int n = static_cast<int>(bits.size());
    std::vector<double> pulses;
    pulses.reserve(n);
    std::vector<B8ZSSubstitutionRecord> subs;

    int i = 0;
    while (i < n) {
        if (i + 8 <= n && bits.substr(i, 8) == "00000000") {
            B8ZSSubstitutionRecord rec;
            rec.start_index = i;
            rec.length = 8;
            rec.previous_polarity = last_polarity;

            std::vector<double> pattern;
            if (last_polarity > 0.0) {
                // 0 0 0 + - 0 - +
                pattern = {zero_voltage_, zero_voltage_, zero_voltage_, positive_voltage_, negative_voltage_, zero_voltage_, negative_voltage_, positive_voltage_};
                rec.rule_applied = "000+-0-+";
                last_polarity = positive_voltage_;
            } else {
                // 0 0 0 - + 0 + -
                pattern = {zero_voltage_, zero_voltage_, zero_voltage_, negative_voltage_, positive_voltage_, zero_voltage_, positive_voltage_, negative_voltage_};
                rec.rule_applied = "000-+0+-";
                last_polarity = negative_voltage_;
            }
            rec.substituted_levels = pattern;
            rec.violation_indices = {i + 3, i + 6};
            rec.bipolar_indices = {i + 4, i + 7};

            subs.push_back(rec);
            pulses.insert(pulses.end(), pattern.begin(), pattern.end());
            i += 8;
        } else {
            char bit = bits[i];
            if (bit == '1') {
                double level = (last_polarity > 0.0) ? negative_voltage_ : positive_voltage_;
                pulses.push_back(level);
                last_polarity = level;
            } else {
                pulses.push_back(zero_voltage_);
            }
            i++;
        }
    }

    return {pulses, subs};
}

std::string B8ZSScrambler::descramble(const std::vector<double>& pulses) {
    if (pulses.empty()) return "";

    double threshold = std::min(std::abs(positive_voltage_), std::abs(negative_voltage_)) * 0.5;
    int n = static_cast<int>(pulses.size());
    std::string recovered(n, '0');

    double last_pol = negative_voltage_;
    int i = 0;

    while (i < n) {
        if (std::abs(pulses[i]) < threshold) {
            // Check if 8-zero substitution pattern begins here
            if (i + 8 <= n) {
                // Indices in block: 0,1,2=0, 3=V, 4=B, 5=0, 6=V, 7=B
                bool z0 = std::abs(pulses[i]) < threshold;
                bool z1 = std::abs(pulses[i + 1]) < threshold;
                bool z2 = std::abs(pulses[i + 2]) < threshold;
                bool v3 = std::abs(pulses[i + 3]) >= threshold;
                bool b4 = std::abs(pulses[i + 4]) >= threshold;
                bool z5 = std::abs(pulses[i + 5]) < threshold;
                bool v6 = std::abs(pulses[i + 6]) >= threshold;
                bool b7 = std::abs(pulses[i + 7]) >= threshold;

                if (z0 && z1 && z2 && v3 && b4 && z5 && v6 && b7) {
                    // Check violation: pulse[i+3] has same sign as last_pol
                    bool v3_same = (pulses[i + 3] * last_pol > 0.0);
                    // b4 has opposite sign of v3
                    bool b4_opp = (pulses[i + 4] * pulses[i + 3] < 0.0);
                    // v6 has same sign as b4 (violates b4)
                    bool v6_same = (pulses[i + 6] * pulses[i + 4] > 0.0);
                    // b7 has opposite sign of v6
                    bool b7_opp = (pulses[i + 7] * pulses[i + 6] < 0.0);

                    if (v3_same && b4_opp && v6_same && b7_opp) {
                        for (int k = 0; k < 8; ++k) {
                            recovered[i + k] = '0';
                        }
                        last_pol = pulses[i + 7];
                        i += 8;
                        continue;
                    }
                }
            }
            recovered[i] = '0';
        } else {
            recovered[i] = '1';
            last_pol = pulses[i];
        }
        i++;
    }

    return recovered;
}

line_coding::SignalWaveform B8ZSScrambler::encode(
    const std::string& bits,
    std::optional<double> initial_polarity
) {
    auto [pulses, subs] = scramble(bits, initial_polarity);
    int n = static_cast<int>(pulses.size());
    int total_pts = n * samples_per_bit_;
    std::vector<double> times;
    std::vector<double> volts;
    times.reserve(total_pts);
    volts.reserve(total_pts);

    double dt = bit_duration_ / samples_per_bit_;
    for (int i = 0; i < n; ++i) {
        double v = pulses[i];
        for (int s = 0; s < samples_per_bit_; ++s) {
            times.push_back((i * samples_per_bit_ + s) * dt);
            volts.push_back(v);
        }
    }

    line_coding::SignalWaveform wf;
    wf.bits = bits;
    wf.time_points = std::move(times);
    wf.voltages = std::move(volts);
    wf.samples_per_bit = samples_per_bit_;
    wf.bit_duration = bit_duration_;
    wf.positive_voltage = positive_voltage_;
    wf.negative_voltage = negative_voltage_;
    wf.zero_voltage = zero_voltage_;
    wf.metadata["scheme"] = "AMI";
    wf.metadata["scrambling"] = "B8ZS";
    wf.metadata["substitutions_count"] = std::to_string(subs.size());

    for (const auto& sub : subs) {
        wf.violation_indices.insert(wf.violation_indices.end(), sub.violation_indices.begin(), sub.violation_indices.end());
        wf.bipolar_indices.insert(wf.bipolar_indices.end(), sub.bipolar_indices.begin(), sub.bipolar_indices.end());
    }

    return wf;
}

std::string B8ZSScrambler::decode(const line_coding::SignalWaveform& waveform) {
    std::vector<double> pulses;
    pulses.reserve(waveform.num_bits());
    for (int i = 0; i < waveform.num_bits(); ++i) {
        auto [t, v] = waveform.get_midpoint_sample(i);
        pulses.push_back(v);
    }
    return descramble(pulses);
}

} // namespace scrambling
} // namespace dc
