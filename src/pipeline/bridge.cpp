#include "pipeline/bridge.hpp"
#include <stdexcept>

namespace dc {
namespace pipeline {

PipelineBridge::PipelineBridge(
    int samples_per_bit,
    double bit_duration,
    double positive_voltage,
    double negative_voltage,
    double zero_voltage
) : samples_per_bit_(samples_per_bit),
    bit_duration_(bit_duration),
    positive_voltage_(positive_voltage),
    negative_voltage_(negative_voltage),
    zero_voltage_(zero_voltage) {}

std::unique_ptr<line_coding::LineEncoder> PipelineBridge::create_encoder(const std::string& scheme) {
    if (scheme == "NRZ-L") {
        return std::make_unique<line_coding::NRZLEncoder>(true, samples_per_bit_, bit_duration_, positive_voltage_, negative_voltage_);
    } else if (scheme == "NRZ-I") {
        return std::make_unique<line_coding::NRZIEncoder>(std::nullopt, samples_per_bit_, bit_duration_, positive_voltage_, negative_voltage_);
    } else if (scheme == "Manchester") {
        return std::make_unique<line_coding::ManchesterEncoder>(line_coding::ManchesterConvention::IEEE, samples_per_bit_, bit_duration_, positive_voltage_, negative_voltage_);
    } else if (scheme == "Differential Manchester") {
        return std::make_unique<line_coding::DifferentialManchesterEncoder>(negative_voltage_, samples_per_bit_, bit_duration_, positive_voltage_, negative_voltage_);
    } else if (scheme == "AMI") {
        return std::make_unique<line_coding::AMIEncoder>(std::nullopt, samples_per_bit_, bit_duration_, positive_voltage_, negative_voltage_, zero_voltage_);
    } else {
        throw std::invalid_argument("Unknown line coding scheme: " + scheme);
    }
}

PipelineResult PipelineBridge::run_analog_to_line_coding(
    const analog::ContinuousSignal& signal,
    double sampling_rate,
    double duration,
    const std::string& modulation,
    int num_bits,
    double step_size,
    const std::string& line_scheme,
    const std::string& scrambling
) {
    PipelineResult res;
    res.analog_signal = signal;
    res.modulation_type = modulation;
    res.line_scheme = line_scheme;
    res.scrambling_scheme = scrambling;

    // Stage 1: Nyquist Sampling
    analog::NyquistSampler sampler;
    res.sampling_result = sampler.sample(signal, sampling_rate, duration);

    // Stage 2: Quantization / Modulation -> Bitstream
    if (modulation == "DM") {
        analog::DeltaModulator dm(step_size, sampling_rate, 0.0);
        auto dm_res = dm.encode_samples(res.sampling_result.sample_values, res.sampling_result.sample_times);
        res.bitstream = dm_res.bitstream;
    } else { // "PCM"
        analog::UniformQuantizer uq(num_bits, -signal.max_frequency(), signal.max_frequency(), "natural");
        // Compute peak-to-peak amplitude from signal
        double v_max = 0.0;
        for (double v : res.sampling_result.sample_values) {
            if (std::abs(v) > v_max) v_max = std::abs(v);
        }
        if (v_max < 0.1) v_max = 1.0;
        analog::UniformQuantizer pcm(num_bits, -v_max * 1.1, v_max * 1.1, "natural");
        auto q_res = pcm.quantize_samples(res.sampling_result.sample_values);
        res.bitstream = q_res.bitstream;
    }

    if (res.bitstream.empty()) {
        res.bitstream = "0";
    }

    // Stage 3: Line Encoding
    auto encoder = create_encoder(line_scheme);
    res.encoded_waveform = encoder->encode(res.bitstream);

    // Stage 4: Scrambling (if requested and applicable to AMI)
    decoder::PhysicalSignalDecoder dec;
    if (scrambling == "B8ZS") {
        scrambling::B8ZSScrambler scrambler(positive_voltage_, negative_voltage_, zero_voltage_, samples_per_bit_, bit_duration_);
        res.scrambled_waveform = scrambler.encode(res.bitstream);
        res.decoded_signal = dec.decode(res.scrambled_waveform.value());
    } else if (scrambling == "HDB3") {
        scrambling::HDB3Scrambler scrambler(positive_voltage_, negative_voltage_, zero_voltage_, samples_per_bit_, bit_duration_);
        res.scrambled_waveform = scrambler.encode(res.bitstream);
        res.decoded_signal = dec.decode(res.scrambled_waveform.value());
    } else {
        res.decoded_signal = dec.decode(res.encoded_waveform);
    }

    // Stage 5: Verification & Metrics
    res.accuracy_pct = decoder::PhysicalSignalDecoder::compute_accuracy(res.bitstream, res.decoded_signal.recovered_bits);
    res.ber = decoder::PhysicalSignalDecoder::compute_ber(res.bitstream, res.decoded_signal.recovered_bits);
    res.verification_passed = (res.bitstream == res.decoded_signal.recovered_bits);

    return res;
}

PipelineResult PipelineBridge::run_bitstream_pipeline(
    const std::string& bitstream,
    const std::string& line_scheme,
    const std::string& scrambling
) {
    PipelineResult res;
    res.bitstream = bitstream;
    res.modulation_type = "Direct Digital";
    res.line_scheme = line_scheme;
    res.scrambling_scheme = scrambling;

    auto encoder = create_encoder(line_scheme);
    res.encoded_waveform = encoder->encode(bitstream);

    decoder::PhysicalSignalDecoder dec;
    if (scrambling == "B8ZS") {
        scrambling::B8ZSScrambler scrambler(positive_voltage_, negative_voltage_, zero_voltage_, samples_per_bit_, bit_duration_);
        res.scrambled_waveform = scrambler.encode(bitstream);
        res.decoded_signal = dec.decode(res.scrambled_waveform.value());
    } else if (scrambling == "HDB3") {
        scrambling::HDB3Scrambler scrambler(positive_voltage_, negative_voltage_, zero_voltage_, samples_per_bit_, bit_duration_);
        res.scrambled_waveform = scrambler.encode(bitstream);
        res.decoded_signal = dec.decode(res.scrambled_waveform.value());
    } else {
        res.decoded_signal = dec.decode(res.encoded_waveform);
    }

    res.accuracy_pct = decoder::PhysicalSignalDecoder::compute_accuracy(bitstream, res.decoded_signal.recovered_bits);
    res.ber = decoder::PhysicalSignalDecoder::compute_ber(bitstream, res.decoded_signal.recovered_bits);
    res.verification_passed = (bitstream == res.decoded_signal.recovered_bits);

    return res;
}

} // namespace pipeline
} // namespace dc
