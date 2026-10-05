#include "line_coding/base.hpp"
#include <stdexcept>

namespace dc {
namespace line_coding {

std::pair<std::vector<double>, std::vector<double>> SignalWaveform::get_bit_slice(int bit_index) const {
    if (bit_index < 0 || bit_index >= num_bits()) {
        throw std::out_of_range("Bit index " + std::to_string(bit_index) + " out of range [0, " + std::to_string(num_bits() - 1) + "]");
    }
    int start = bit_index * samples_per_bit;
    int end = start + samples_per_bit;
    std::vector<double> t_slice(time_points.begin() + start, time_points.begin() + end);
    std::vector<double> v_slice(voltages.begin() + start, voltages.begin() + end);
    return {t_slice, v_slice};
}

std::pair<double, double> SignalWaveform::get_midpoint_sample(int bit_index) const {
    if (bit_index < 0 || bit_index >= num_bits()) {
        throw std::out_of_range("Bit index " + std::to_string(bit_index) + " out of range [0, " + std::to_string(num_bits() - 1) + "]");
    }
    int mid_idx = bit_index * samples_per_bit + (samples_per_bit / 2);
    return {time_points[mid_idx], voltages[mid_idx]};
}

LineEncoder::LineEncoder(
    int samples_per_bit,
    double bit_duration,
    double positive_voltage,
    double negative_voltage,
    double zero_voltage
) : samples_per_bit_(samples_per_bit),
    bit_duration_(bit_duration),
    positive_voltage_(positive_voltage),
    negative_voltage_(negative_voltage),
    zero_voltage_(zero_voltage) {
    if (samples_per_bit < 2) {
        throw std::invalid_argument("samples_per_bit must be at least 2, got " + std::to_string(samples_per_bit));
    }
    if (bit_duration <= 0.0) {
        throw std::invalid_argument("bit_duration must be positive, got " + std::to_string(bit_duration));
    }
}

void LineEncoder::validate_input(const std::string& bits) {
    if (bits.empty()) {
        throw std::invalid_argument("Input bitstream cannot be empty.");
    }
    for (char c : bits) {
        if (c != '0' && c != '1') {
            throw std::invalid_argument(std::string("Input bitstream contains non-binary character: ") + c);
        }
    }
}

} // namespace line_coding
} // namespace dc
