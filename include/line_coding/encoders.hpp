#pragma once

#include "line_coding/base.hpp"
#include <optional>

namespace dc {
namespace line_coding {

class NRZLEncoder : public LineEncoder {
public:
    explicit NRZLEncoder(
        bool zero_is_positive = true,
        int samples_per_bit = 100,
        double bit_duration = 1.0,
        double positive_voltage = 1.0,
        double negative_voltage = -1.0
    );

    std::string scheme_name() const override { return "NRZ-L"; }
    SignalWaveform encode(const std::string& bits) override;
    std::string decode(const SignalWaveform& waveform) override;

    double bit_to_voltage(char bit) const;

private:
    bool zero_is_positive_;
};

class NRZIEncoder : public LineEncoder {
public:
    explicit NRZIEncoder(
        std::optional<double> initial_voltage = std::nullopt,
        int samples_per_bit = 100,
        double bit_duration = 1.0,
        double positive_voltage = 1.0,
        double negative_voltage = -1.0
    );

    std::string scheme_name() const override { return "NRZ-I"; }
    SignalWaveform encode(const std::string& bits) override;
    std::string decode(const SignalWaveform& waveform) override;
    std::string decode(const SignalWaveform& waveform, std::optional<double> initial_voltage);

private:
    std::optional<double> initial_voltage_;
};

enum class ManchesterConvention {
    IEEE,    // 0 -> +V then -V; 1 -> -V then +V
    Thomas   // 0 -> -V then +V; 1 -> +V then -V
};

class ManchesterEncoder : public LineEncoder {
public:
    explicit ManchesterEncoder(
        ManchesterConvention convention = ManchesterConvention::IEEE,
        int samples_per_bit = 100,
        double bit_duration = 1.0,
        double positive_voltage = 1.0,
        double negative_voltage = -1.0
    );

    std::string scheme_name() const override {
        return convention_ == ManchesterConvention::IEEE ? "Manchester (IEEE 802.3)" : "Manchester (G.E. Thomas)";
    }
    SignalWaveform encode(const std::string& bits) override;
    std::string decode(const SignalWaveform& waveform) override;

    std::pair<double, double> bit_to_half_voltages(char bit) const;
    ManchesterConvention convention() const { return convention_; }

private:
    ManchesterConvention convention_;
};

class DifferentialManchesterEncoder : public LineEncoder {
public:
    explicit DifferentialManchesterEncoder(
        double initial_voltage = -1.0,
        int samples_per_bit = 100,
        double bit_duration = 1.0,
        double positive_voltage = 1.0,
        double negative_voltage = -1.0
    );

    std::string scheme_name() const override { return "Differential Manchester"; }
    SignalWaveform encode(const std::string& bits) override;
    std::string decode(const SignalWaveform& waveform) override;

private:
    double initial_voltage_;
};

class AMIEncoder : public LineEncoder {
public:
    explicit AMIEncoder(
        std::optional<double> initial_polarity = std::nullopt,
        int samples_per_bit = 100,
        double bit_duration = 1.0,
        double positive_voltage = 1.0,
        double negative_voltage = -1.0,
        double zero_voltage = 0.0
    );

    std::string scheme_name() const override { return "AMI"; }
    SignalWaveform encode(const std::string& bits) override;
    std::string decode(const SignalWaveform& waveform) override;

private:
    std::optional<double> initial_polarity_;
};

} // namespace line_coding
} // namespace dc
