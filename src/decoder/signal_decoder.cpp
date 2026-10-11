#include "decoder/signal_decoder.hpp"
#include "scrambling/b8zs.hpp"
#include "scrambling/hdb3.hpp"
#include <cmath>
#include <stdexcept>
#include <algorithm>

namespace dc {
namespace decoder {

PhysicalSignalDecoder::PhysicalSignalDecoder(double slicing_margin)
    : slicing_margin_(slicing_margin) {}

DecodedSignal PhysicalSignalDecoder::decode_nrz_l(const line_coding::SignalWaveform& wf, bool zero_is_positive) {
    double threshold = (wf.positive_voltage + wf.negative_voltage) / 2.0;
    std::string bits;
    std::vector<double> levels;
    bits.reserve(wf.num_bits());
    levels.reserve(wf.num_bits());

    for (int i = 0; i < wf.num_bits(); ++i) {
        auto [t, v] = wf.get_midpoint_sample(i);
        levels.push_back(v);
        if (zero_is_positive) {
            bits.push_back(v >= threshold ? '0' : '1');
        } else {
            bits.push_back(v >= threshold ? '1' : '0');
        }
    }

    return DecodedSignal{bits, "NRZ-L", "None", wf.num_bits(), 100.0, levels};
}

DecodedSignal PhysicalSignalDecoder::decode_nrz_i(const line_coding::SignalWaveform& wf, std::optional<double> initial_voltage) {
    double threshold = (wf.positive_voltage + wf.negative_voltage) / 2.0;
    double last_level = initial_voltage.value_or(wf.negative_voltage);
    std::string bits;
    std::vector<double> levels;
    bits.reserve(wf.num_bits());
    levels.reserve(wf.num_bits());

    for (int i = 0; i < wf.num_bits(); ++i) {
        auto [t, v] = wf.get_midpoint_sample(i);
        levels.push_back(v);
        bool current_high = (v >= threshold);
        bool last_high = (last_level >= threshold);

        bits.push_back(current_high != last_high ? '1' : '0');
        last_level = v;
    }

    return DecodedSignal{bits, "NRZ-I", "None", wf.num_bits(), 100.0, levels};
}

DecodedSignal PhysicalSignalDecoder::decode_manchester(const line_coding::SignalWaveform& wf, const std::string& convention) {
    int spb = wf.samples_per_bit;
    int q1 = spb / 4;
    int q3 = (3 * spb) / 4;
    double threshold = (wf.positive_voltage + wf.negative_voltage) / 2.0;

    std::string bits;
    std::vector<double> levels;
    bits.reserve(wf.num_bits());
    levels.reserve(wf.num_bits());

    bool is_ieee = (convention == "ieee" || convention == "IEEE");

    for (int i = 0; i < wf.num_bits(); ++i) {
        int idx1 = i * spb + q1;
        int idx2 = i * spb + q3;
        double v1 = wf.voltages[idx1];
        double v2 = wf.voltages[idx2];
        levels.push_back(v1);

        bool first_high = (v1 >= threshold);
        bool second_high = (v2 >= threshold);

        if (is_ieee) {
            bits.push_back((first_high && !second_high) ? '0' : '1');
        } else {
            bits.push_back((!first_high && second_high) ? '0' : '1');
        }
    }

    return DecodedSignal{bits, is_ieee ? "Manchester (IEEE 802.3)" : "Manchester (G.E. Thomas)", "None", wf.num_bits(), 100.0, levels};
}

DecodedSignal PhysicalSignalDecoder::decode_differential_manchester(const line_coding::SignalWaveform& wf) {
    int spb = wf.samples_per_bit;
    int q1 = spb / 4;
    int q3 = (3 * spb) / 4;
    double threshold = (wf.positive_voltage + wf.negative_voltage) / 2.0;
    double last_half = wf.negative_voltage;

    std::string bits;
    std::vector<double> levels;
    bits.reserve(wf.num_bits());
    levels.reserve(wf.num_bits());

    for (int i = 0; i < wf.num_bits(); ++i) {
        int idx1 = i * spb + q1;
        double v1 = wf.voltages[idx1];
        levels.push_back(v1);

        bool current_first_high = (v1 >= threshold);
        bool last_second_high = (last_half >= threshold);

        bits.push_back(current_first_high != last_second_high ? '0' : '1');
        int idx2 = i * spb + q3;
        last_half = wf.voltages[idx2];
    }

    return DecodedSignal{bits, "Differential Manchester", "None", wf.num_bits(), 100.0, levels};
}

DecodedSignal PhysicalSignalDecoder::decode_ami(const line_coding::SignalWaveform& wf) {
    double threshold = std::min(std::abs(wf.positive_voltage), std::abs(wf.negative_voltage)) * slicing_margin_;
    std::string bits;
    std::vector<double> levels;
    bits.reserve(wf.num_bits());
    levels.reserve(wf.num_bits());

    for (int i = 0; i < wf.num_bits(); ++i) {
        auto [t, v] = wf.get_midpoint_sample(i);
        levels.push_back(v);
        bits.push_back(std::abs(v) > threshold ? '1' : '0');
    }

    return DecodedSignal{bits, "AMI", "None", wf.num_bits(), 100.0, levels};
}

DecodedSignal PhysicalSignalDecoder::decode_b8zs(const line_coding::SignalWaveform& wf) {
    std::vector<double> levels;
    levels.reserve(wf.num_bits());
    for (int i = 0; i < wf.num_bits(); ++i) {
        auto [t, v] = wf.get_midpoint_sample(i);
        levels.push_back(v);
    }
    scrambling::B8ZSScrambler scrambler(wf.positive_voltage, wf.negative_voltage, wf.zero_voltage);
    std::string bits = scrambler.descramble(levels);

    return DecodedSignal{bits, "AMI", "B8ZS", wf.num_bits(), 100.0, levels};
}

DecodedSignal PhysicalSignalDecoder::decode_hdb3(const line_coding::SignalWaveform& wf) {
    std::vector<double> levels;
    levels.reserve(wf.num_bits());
    for (int i = 0; i < wf.num_bits(); ++i) {
        auto [t, v] = wf.get_midpoint_sample(i);
        levels.push_back(v);
    }
    scrambling::HDB3Scrambler scrambler(wf.positive_voltage, wf.negative_voltage, wf.zero_voltage);
    std::string bits = scrambler.descramble(levels);

    return DecodedSignal{bits, "AMI", "HDB3", wf.num_bits(), 100.0, levels};
}

DecodedSignal PhysicalSignalDecoder::decode(
    const line_coding::SignalWaveform& wf,
    const std::string& scheme_override,
    const std::string& scramble_override
) {
    std::string scheme = scheme_override;
    if (scheme.empty()) {
        auto it = wf.metadata.find("scheme");
        if (it != wf.metadata.end()) {
            scheme = it->second;
        } else {
            scheme = "NRZ-L";
        }
    }

    std::string scramble = scramble_override;
    if (scramble.empty()) {
        auto it = wf.metadata.find("scrambling");
        if (it != wf.metadata.end()) {
            scramble = it->second;
        }
    }

    if (scramble == "B8ZS") {
        return decode_b8zs(wf);
    } else if (scramble == "HDB3") {
        return decode_hdb3(wf);
    }

    if (scheme == "NRZ-L") {
        bool zero_pos = true;
        auto it = wf.metadata.find("zero_is_positive");
        if (it != wf.metadata.end() && it->second == "false") {
            zero_pos = false;
        }
        return decode_nrz_l(wf, zero_pos);
    } else if (scheme == "NRZ-I") {
        return decode_nrz_i(wf);
    } else if (scheme.find("Manchester") != std::string::npos && scheme.find("Differential") == std::string::npos) {
        std::string conv = "ieee";
        auto it = wf.metadata.find("convention");
        if (it != wf.metadata.end()) {
            conv = it->second;
        }
        return decode_manchester(wf, conv);
    } else if (scheme.find("Differential Manchester") != std::string::npos) {
        return decode_differential_manchester(wf);
    } else if (scheme == "AMI") {
        return decode_ami(wf);
    } else {
        return decode_nrz_l(wf);
    }
}

double PhysicalSignalDecoder::compute_accuracy(const std::string& original, const std::string& decoded) {
    if (original.empty() && decoded.empty()) return 100.0;
    if (original.size() != decoded.size()) {
        int matches = 0;
        size_t min_len = std::min(original.size(), decoded.size());
        size_t max_len = std::max(original.size(), decoded.size());
        for (size_t i = 0; i < min_len; ++i) {
            if (original[i] == decoded[i]) matches++;
        }
        return (static_cast<double>(matches) / max_len) * 100.0;
    }
    int matches = 0;
    for (size_t i = 0; i < original.size(); ++i) {
        if (original[i] == decoded[i]) matches++;
    }
    return (static_cast<double>(matches) / original.size()) * 100.0;
}

double PhysicalSignalDecoder::compute_ber(const std::string& original, const std::string& decoded) {
    return (100.0 - compute_accuracy(original, decoded)) / 100.0;
}

} // namespace decoder
} // namespace dc
