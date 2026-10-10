#include "scrambling/hdb3.hpp"
#include <cmath>
#include <stdexcept>

namespace dc {
namespace scrambling {

HDB3Scrambler::HDB3Scrambler(
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

std::pair<std::vector<double>, std::vector<HDB3SubstitutionRecord>> HDB3Scrambler::scramble(
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
    int pulses_since_last = 0;
    int n = static_cast<int>(bits.size());
    std::vector<double> pulses;
    pulses.reserve(n);
    std::vector<HDB3SubstitutionRecord> subs;

    int i = 0;
    while (i < n) {
        if (i + 4 <= n && bits.substr(i, 4) == "0000") {
            HDB3SubstitutionRecord rec;
            rec.start_index = i;
            rec.length = 4;
            rec.previous_polarity = last_polarity;
            rec.pulses_since_last = pulses_since_last;

            std::vector<double> pattern;
            if (pulses_since_last % 2 != 0) {
                // Odd parity: 0 0 0 V
                double v = last_polarity; // same polarity as previous
                pattern = {zero_voltage_, zero_voltage_, zero_voltage_, v};
                rec.rule_applied = "000V";
                rec.violation_indices = {i + 3};
                last_polarity = v;
            } else {
                // Even parity: B 0 0 V
                double b = (last_polarity > 0.0) ? negative_voltage_ : positive_voltage_; // opposite
                double v = b; // violation of B
                pattern = {b, zero_voltage_, zero_voltage_, v};
                rec.rule_applied = "B00V";
                rec.bipolar_indices = {i};
                rec.violation_indices = {i + 3};
                last_polarity = v;
            }
            rec.substituted_levels = pattern;
            subs.push_back(rec);

            pulses.insert(pulses.end(), pattern.begin(), pattern.end());
            pulses_since_last = 0;
            i += 4;
        } else {
            char bit = bits[i];
            if (bit == '1') {
                double level = (last_polarity > 0.0) ? negative_voltage_ : positive_voltage_;
                pulses.push_back(level);
                last_polarity = level;
                pulses_since_last++;
            } else {
                pulses.push_back(zero_voltage_);
            }
            i++;
        }
    }

    return {pulses, subs};
}

std::string HDB3Scrambler::descramble(const std::vector<double>& pulses) {
    if (pulses.empty()) return "";

    double threshold = std::min(std::abs(positive_voltage_), std::abs(negative_voltage_)) * 0.5;
    int n = static_cast<int>(pulses.size());
    std::string recovered;
    recovered.reserve(n);

    // Initial pass: treat non-zero pulses as '1', zeros as '0'
    for (double p : pulses) {
        recovered.push_back(std::abs(p) >= threshold ? '1' : '0');
    }

    // Secondary pass: scan for bipolar violations (V)
    double last_pol = negative_voltage_;
    int last_non_zero_idx = -1;

    for (int i = 0; i < n; ++i) {
        if (std::abs(pulses[i]) >= threshold) {
            double current_pol = pulses[i];
            // Check if current pulse has the SAME polarity as the previous non-zero pulse
            if (current_pol * last_pol > 0.0 && last_non_zero_idx >= 0) {
                // Bipolar Violation detected at index i!
                // Pattern could be 000V or B00V
                if (i >= 3) {
                    bool z1 = std::abs(pulses[i - 1]) < threshold;
                    bool z2 = std::abs(pulses[i - 2]) < threshold;
                    if (z1 && z2) {
                        bool is_b00v = (std::abs(pulses[i - 3]) >= threshold);
                        if (is_b00v) {
                            // B 0 0 V: clear all 4 positions
                            recovered[i - 3] = '0';
                            recovered[i - 2] = '0';
                            recovered[i - 1] = '0';
                            recovered[i] = '0';
                        } else {
                            // 0 0 0 V: clear all 4 positions
                            recovered[i - 3] = '0';
                            recovered[i - 2] = '0';
                            recovered[i - 1] = '0';
                            recovered[i] = '0';
                        }
                    }
                }
            }
            last_pol = current_pol;
            last_non_zero_idx = i;
        }
    }

    return recovered;
}

line_coding::SignalWaveform HDB3Scrambler::encode(
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
    wf.metadata["scrambling"] = "HDB3";
    wf.metadata["substitutions_count"] = std::to_string(subs.size());

    for (const auto& sub : subs) {
        wf.violation_indices.insert(wf.violation_indices.end(), sub.violation_indices.begin(), sub.violation_indices.end());
        wf.bipolar_indices.insert(wf.bipolar_indices.end(), sub.bipolar_indices.begin(), sub.bipolar_indices.end());
    }

    return wf;
}

std::string HDB3Scrambler::decode(const line_coding::SignalWaveform& waveform) {
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
