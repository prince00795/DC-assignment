#pragma once

#include <vector>
#include <string>

namespace dc {
namespace analog {

struct QuantizedSample {
    int index = 0;
    double original_value = 0.0;
    double quantized_value = 0.0;
    double error = 0.0;
    std::string binary_code;
};

struct QuantizationResult {
    std::vector<QuantizedSample> samples;
    std::vector<double> quantized_samples;
    std::string bitstream;
    int num_bits = 3;
    int num_levels = 8;
    double step_size = 0.0;
    double v_min = -1.0;
    double v_max = 1.0;
    double theoretical_sqnr_db = 0.0;
    double empirical_sqnr_db = 0.0;
    double mse = 0.0;
};

class UniformQuantizer {
public:
    explicit UniformQuantizer(
        int num_bits = 3,
        double v_min = -1.0,
        double v_max = 1.0,
        std::string encoding_type = "natural"
    );

    int num_bits() const { return num_bits_; }
    int num_levels() const { return num_levels_; }
    double step_size() const { return step_size_; }
    double v_min() const { return v_min_; }
    double v_max() const { return v_max_; }
    const std::string& encoding_type() const { return encoding_type_; }

    double theoretical_sqnr_db() const { return 6.02 * num_bits_ + 1.76; }

    QuantizationResult quantize_samples(const std::vector<double>& analog_samples) const;
    std::vector<double> decode_bitstream(const std::string& bitstream) const;

    int quantize_single(double val, double& mid_voltage, std::string& code) const;

private:
    int num_bits_;
    int num_levels_;
    double v_min_;
    double v_max_;
    double step_size_;
    std::string encoding_type_;

    std::string index_to_code(int idx) const;
    int code_to_index(const std::string& code) const;
};

} // namespace analog
} // namespace dc
