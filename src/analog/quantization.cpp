#include "analog/quantization.hpp"
#include <cmath>
#include <stdexcept>
#include <bitset>
#include <algorithm>

namespace dc {
namespace analog {

UniformQuantizer::UniformQuantizer(
    int num_bits,
    double v_min,
    double v_max,
    std::string encoding_type
) : num_bits_(num_bits),
    v_min_(v_min),
    v_max_(v_max),
    encoding_type_(std::move(encoding_type)) {
    if (num_bits < 1 || num_bits > 16) {
        throw std::invalid_argument("num_bits must be between 1 and 16, got " + std::to_string(num_bits));
    }
    if (v_min >= v_max) {
        throw std::invalid_argument("v_min must be strictly less than v_max");
    }
    num_levels_ = 1 << num_bits;
    step_size_ = (v_max_ - v_min_) / num_levels_;
}

std::string UniformQuantizer::index_to_code(int idx) const {
    if (encoding_type_ == "gray") {
        int g = idx ^ (idx >> 1);
        std::string s;
        for (int b = num_bits_ - 1; b >= 0; --b) {
            s.push_back((g & (1 << b)) ? '1' : '0');
        }
        return s;
    } else if (encoding_type_ == "twos_complement") {
        // Shift [0, 2^n - 1] to signed [-2^(n-1), 2^(n-1) - 1]
        int signed_val = idx - (num_levels_ / 2);
        int mask = (1 << num_bits_) - 1;
        int bits = signed_val & mask;
        std::string s;
        for (int b = num_bits_ - 1; b >= 0; --b) {
            s.push_back((bits & (1 << b)) ? '1' : '0');
        }
        return s;
    } else { // "natural"
        std::string s;
        for (int b = num_bits_ - 1; b >= 0; --b) {
            s.push_back((idx & (1 << b)) ? '1' : '0');
        }
        return s;
    }
}

int UniformQuantizer::code_to_index(const std::string& code) const {
    if (static_cast<int>(code.size()) != num_bits_) {
        throw std::invalid_argument("Invalid binary code length for quantization");
    }
    if (encoding_type_ == "gray") {
        int g = 0;
        for (char c : code) {
            g = (g << 1) | (c == '1' ? 1 : 0);
        }
        // Gray to binary conversion
        int b = 0;
        for (int v = g; v > 0; v >>= 1) {
            b ^= v;
        }
        return b;
    } else if (encoding_type_ == "twos_complement") {
        int raw = 0;
        for (char c : code) {
            raw = (raw << 1) | (c == '1' ? 1 : 0);
        }
        // Sign extend if MSB is 1
        if (raw & (1 << (num_bits_ - 1))) {
            raw -= (1 << num_bits_);
        }
        return raw + (num_levels_ / 2);
    } else { // natural
        int b = 0;
        for (char c : code) {
            b = (b << 1) | (c == '1' ? 1 : 0);
        }
        return b;
    }
}

int UniformQuantizer::quantize_single(double val, double& mid_voltage, std::string& code) const {
    double clamped = std::clamp(val, v_min_, v_max_);
    int idx = static_cast<int>(std::floor((clamped - v_min_) / step_size_));
    if (idx >= num_levels_) {
        idx = num_levels_ - 1;
    }
    if (idx < 0) {
        idx = 0;
    }
    mid_voltage = v_min_ + (idx + 0.5) * step_size_;
    code = index_to_code(idx);
    return idx;
}

QuantizationResult UniformQuantizer::quantize_samples(const std::vector<double>& analog_samples) const {
    QuantizationResult res;
    res.num_bits = num_bits_;
    res.num_levels = num_levels_;
    res.step_size = step_size_;
    res.v_min = v_min_;
    res.v_max = v_max_;
    res.theoretical_sqnr_db = theoretical_sqnr_db();

    if (analog_samples.empty()) {
        return res;
    }

    res.samples.reserve(analog_samples.size());
    res.quantized_samples.reserve(analog_samples.size());
    res.bitstream.reserve(analog_samples.size() * num_bits_);

    double total_err_sq = 0.0;
    double total_sig_sq = 0.0;

    for (double orig : analog_samples) {
        double v_q = 0.0;
        std::string code;
        int idx = quantize_single(orig, v_q, code);
        double err = orig - v_q;

        res.samples.push_back(QuantizedSample{idx, orig, v_q, err, code});
        res.quantized_samples.push_back(v_q);
        res.bitstream.append(code);

        total_err_sq += err * err;
        total_sig_sq += orig * orig;
    }

    size_t count = analog_samples.size();
    res.mse = total_err_sq / count;
    double sig_pow = total_sig_sq / count;

    if (res.mse > 1e-12 && sig_pow > 1e-12) {
        res.empirical_sqnr_db = 10.0 * std::log10(sig_pow / res.mse);
    } else if (sig_pow <= 1e-12) {
        res.empirical_sqnr_db = 0.0;
    } else {
        res.empirical_sqnr_db = 100.0;
    }

    return res;
}

std::vector<double> UniformQuantizer::decode_bitstream(const std::string& bitstream) const {
    if (bitstream.size() % num_bits_ != 0) {
        throw std::invalid_argument("Bitstream length is not a multiple of num_bits");
    }
    int count = static_cast<int>(bitstream.size() / num_bits_);
    std::vector<double> recovered;
    recovered.reserve(count);

    for (int i = 0; i < count; ++i) {
        std::string chunk = bitstream.substr(i * num_bits_, num_bits_);
        int idx = code_to_index(chunk);
        double v = v_min_ + (idx + 0.5) * step_size_;
        recovered.push_back(v);
    }
    return recovered;
}

} // namespace analog
} // namespace dc
