#pragma once

#include "line_coding/base.hpp"
#include <string>
#include <vector>
#include <optional>

namespace dc {
namespace decoder {

struct DecodedSignal {
    std::string recovered_bits;
    std::string line_scheme;
    std::string scrambling_scheme;
    int bit_count = 0;
    double confidence_pct = 100.0;
    std::vector<double> sampled_levels;
};

class PhysicalSignalDecoder {
public:
    explicit PhysicalSignalDecoder(double slicing_margin = 0.5);

    DecodedSignal decode_nrz_l(const line_coding::SignalWaveform& wf, bool zero_is_positive = true);
    DecodedSignal decode_nrz_i(const line_coding::SignalWaveform& wf, std::optional<double> initial_voltage = std::nullopt);
    DecodedSignal decode_manchester(const line_coding::SignalWaveform& wf, const std::string& convention = "ieee");
    DecodedSignal decode_differential_manchester(const line_coding::SignalWaveform& wf);
    DecodedSignal decode_ami(const line_coding::SignalWaveform& wf);
    DecodedSignal decode_b8zs(const line_coding::SignalWaveform& wf);
    DecodedSignal decode_hdb3(const line_coding::SignalWaveform& wf);

    DecodedSignal decode(
        const line_coding::SignalWaveform& wf,
        const std::string& scheme_override = "",
        const std::string& scramble_override = ""
    );

    static double compute_accuracy(const std::string& original, const std::string& decoded);
    static double compute_ber(const std::string& original, const std::string& decoded);

private:
    double slicing_margin_;
};

} // namespace decoder
} // namespace dc
