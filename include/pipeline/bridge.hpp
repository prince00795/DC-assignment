#pragma once

#include "analog/continuous_signal.hpp"
#include "analog/sampling.hpp"
#include "analog/quantization.hpp"
#include "analog/delta_modulation.hpp"
#include "line_coding/base.hpp"
#include "line_coding/encoders.hpp"
#include "scrambling/b8zs.hpp"
#include "scrambling/hdb3.hpp"
#include "decoder/signal_decoder.hpp"
#include <memory>
#include <optional>

namespace dc {
namespace pipeline {

struct PipelineResult {
    analog::ContinuousSignal analog_signal;
    analog::SamplingResult sampling_result;
    std::string bitstream;
    line_coding::SignalWaveform encoded_waveform;
    std::optional<line_coding::SignalWaveform> scrambled_waveform;
    decoder::DecodedSignal decoded_signal;
    double ber = 0.0;
    double accuracy_pct = 100.0;
    bool verification_passed = true;
    std::string modulation_type;
    std::string line_scheme;
    std::string scrambling_scheme;
};

class PipelineBridge {
public:
    explicit PipelineBridge(
        int samples_per_bit = 100,
        double bit_duration = 1.0,
        double positive_voltage = 1.0,
        double negative_voltage = -1.0,
        double zero_voltage = 0.0
    );

    PipelineResult run_analog_to_line_coding(
        const analog::ContinuousSignal& signal,
        double sampling_rate = 20.0,
        double duration = 1.0,
        const std::string& modulation = "PCM", // "PCM" or "DM"
        int num_bits = 3,                      // for PCM
        double step_size = 0.25,               // for DM
        const std::string& line_scheme = "AMI",
        const std::string& scrambling = "None" // "None", "B8ZS", "HDB3"
    );

    PipelineResult run_bitstream_pipeline(
        const std::string& bitstream,
        const std::string& line_scheme = "AMI",
        const std::string& scrambling = "None"
    );

private:
    int samples_per_bit_;
    double bit_duration_;
    double positive_voltage_;
    double negative_voltage_;
    double zero_voltage_;

    std::unique_ptr<line_coding::LineEncoder> create_encoder(const std::string& scheme);
};

} // namespace pipeline
} // namespace dc
