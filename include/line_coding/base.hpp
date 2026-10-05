#pragma once

#include <string>
#include <vector>
#include <map>
#include <utility>
#include <memory>

namespace dc {
namespace line_coding {

struct SignalWaveform {
    std::string bits;
    std::vector<double> time_points;
    std::vector<double> voltages;
    int samples_per_bit = 100;
    double bit_duration = 1.0;
    double positive_voltage = 1.0;
    double negative_voltage = -1.0;
    double zero_voltage = 0.0;
    std::map<std::string, std::string> metadata;
    std::vector<int> violation_indices;
    std::vector<int> bipolar_indices;

    double total_duration() const {
        return static_cast<double>(bits.size()) * bit_duration;
    }

    int num_bits() const {
        return static_cast<int>(bits.size());
    }

    int total_samples() const {
        return static_cast<int>(voltages.size());
    }

    std::pair<std::vector<double>, std::vector<double>> get_bit_slice(int bit_index) const;
    std::pair<double, double> get_midpoint_sample(int bit_index) const;
};

class LineEncoder {
public:
    virtual ~LineEncoder() = default;

    LineEncoder(
        int samples_per_bit = 100,
        double bit_duration = 1.0,
        double positive_voltage = 1.0,
        double negative_voltage = -1.0,
        double zero_voltage = 0.0
    );

    virtual std::string scheme_name() const = 0;
    virtual SignalWaveform encode(const std::string& bits) = 0;
    virtual std::string decode(const SignalWaveform& waveform) = 0;

    int samples_per_bit() const { return samples_per_bit_; }
    double bit_duration() const { return bit_duration_; }
    double positive_voltage() const { return positive_voltage_; }
    double negative_voltage() const { return negative_voltage_; }
    double zero_voltage() const { return zero_voltage_; }

protected:
    int samples_per_bit_;
    double bit_duration_;
    double positive_voltage_;
    double negative_voltage_;
    double zero_voltage_;

    static void validate_input(const std::string& bits);
};

} // namespace line_coding
} // namespace dc
