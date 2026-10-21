#include "line_coding/encoders.hpp"
#include <cmath>
#include <stdexcept>

namespace dc {
namespace line_coding {

// -------------------------------------------------------------
// NRZ-L
// -------------------------------------------------------------
NRZLEncoder::NRZLEncoder(
    bool zero_is_positive,
    int samples_per_bit,
    double bit_duration,
    double positive_voltage,
    double negative_voltage
) : LineEncoder(samples_per_bit, bit_duration, positive_voltage, negative_voltage, 0.0),
    zero_is_positive_(zero_is_positive) {}

double NRZLEncoder::bit_to_voltage(char bit) const {
    if (bit == '0') {
        return zero_is_positive_ ? positive_voltage_ : negative_voltage_;
    } else {
        return zero_is_positive_ ? negative_voltage_ : positive_voltage_;
    }
}

SignalWaveform NRZLEncoder::encode(const std::string& bits) {
    validate_input(bits);
    int n = static_cast<int>(bits.size());
    int total_pts = n * samples_per_bit_;
    std::vector<double> times;
    std::vector<double> volts;
    times.reserve(total_pts);
    volts.reserve(total_pts);

    double dt = bit_duration_ / samples_per_bit_;
    for (int i = 0; i < n; ++i) {
        double v = bit_to_voltage(bits[i]);
        for (int s = 0; s < samples_per_bit_; ++s) {
            times.push_back((i * samples_per_bit_ + s) * dt);
            volts.push_back(v);
        }
    }

    SignalWaveform wf;
    wf.bits = bits;
    wf.time_points = std::move(times);
    wf.voltages = std::move(volts);
    wf.samples_per_bit = samples_per_bit_;
    wf.bit_duration = bit_duration_;
    wf.positive_voltage = positive_voltage_;
    wf.negative_voltage = negative_voltage_;
    wf.zero_voltage = zero_voltage_;
    wf.metadata["scheme"] = "NRZ-L";
    wf.metadata["zero_is_positive"] = zero_is_positive_ ? "true" : "false";
    return wf;
}

std::string NRZLEncoder::decode(const SignalWaveform& waveform) {
    double threshold = (positive_voltage_ + negative_voltage_) / 2.0;
    std::string recovered;
    recovered.reserve(waveform.num_bits());

    for (int i = 0; i < waveform.num_bits(); ++i) {
        auto [t, v] = waveform.get_midpoint_sample(i);
        if (zero_is_positive_) {
            recovered.push_back(v >= threshold ? '0' : '1');
        } else {
            recovered.push_back(v >= threshold ? '1' : '0');
        }
    }
    return recovered;
}

// -------------------------------------------------------------
// NRZ-I
// -------------------------------------------------------------
NRZIEncoder::NRZIEncoder(
    std::optional<double> initial_voltage,
    int samples_per_bit,
    double bit_duration,
    double positive_voltage,
    double negative_voltage
) : LineEncoder(samples_per_bit, bit_duration, positive_voltage, negative_voltage, 0.0),
    initial_voltage_(initial_voltage) {}

SignalWaveform NRZIEncoder::encode(const std::string& bits) {
    validate_input(bits);
    int n = static_cast<int>(bits.size());
    int total_pts = n * samples_per_bit_;
    std::vector<double> times;
    std::vector<double> volts;
    times.reserve(total_pts);
    volts.reserve(total_pts);

    double current_level = initial_voltage_.value_or(negative_voltage_);
    double dt = bit_duration_ / samples_per_bit_;

    for (int i = 0; i < n; ++i) {
        char bit = bits[i];
        if (bit == '1') {
            current_level = (std::abs(current_level - positive_voltage_) < 1e-6) ? negative_voltage_ : positive_voltage_;
        }
        for (int s = 0; s < samples_per_bit_; ++s) {
            times.push_back((i * samples_per_bit_ + s) * dt);
            volts.push_back(current_level);
        }
    }

    SignalWaveform wf;
    wf.bits = bits;
    wf.time_points = std::move(times);
    wf.voltages = std::move(volts);
    wf.samples_per_bit = samples_per_bit_;
    wf.bit_duration = bit_duration_;
    wf.positive_voltage = positive_voltage_;
    wf.negative_voltage = negative_voltage_;
    wf.zero_voltage = zero_voltage_;
    wf.metadata["scheme"] = "NRZ-I";
    wf.metadata["initial_voltage"] = std::to_string(initial_voltage_.value_or(negative_voltage_));
    return wf;
}

std::string NRZIEncoder::decode(const SignalWaveform& waveform) {
    return decode(waveform, initial_voltage_);
}

std::string NRZIEncoder::decode(const SignalWaveform& waveform, std::optional<double> initial_voltage) {
    double threshold = (positive_voltage_ + negative_voltage_) / 2.0;
    double last_level = initial_voltage.value_or(negative_voltage_);
    std::string recovered;
    recovered.reserve(waveform.num_bits());

    for (int i = 0; i < waveform.num_bits(); ++i) {
        auto [t, v] = waveform.get_midpoint_sample(i);
        bool current_is_pos = (v >= threshold);
        bool last_is_pos = (last_level >= threshold);

        if (current_is_pos != last_is_pos) {
            recovered.push_back('1');
        } else {
            recovered.push_back('0');
        }
        last_level = v;
    }
    return recovered;
}

// -------------------------------------------------------------
// Manchester
// -------------------------------------------------------------
ManchesterEncoder::ManchesterEncoder(
    ManchesterConvention convention,
    int samples_per_bit,
    double bit_duration,
    double positive_voltage,
    double negative_voltage
) : LineEncoder(samples_per_bit, bit_duration, positive_voltage, negative_voltage, 0.0),
    convention_(convention) {}

std::pair<double, double> ManchesterEncoder::bit_to_half_voltages(char bit) const {
    if (bit == '0') {
        if (convention_ == ManchesterConvention::IEEE) {
            return {positive_voltage_, negative_voltage_};
        } else {
            return {negative_voltage_, positive_voltage_};
        }
    } else {
        if (convention_ == ManchesterConvention::IEEE) {
            return {negative_voltage_, positive_voltage_};
        } else {
            return {positive_voltage_, negative_voltage_};
        }
    }
}

SignalWaveform ManchesterEncoder::encode(const std::string& bits) {
    validate_input(bits);
    int n = static_cast<int>(bits.size());
    int total_pts = n * samples_per_bit_;
    std::vector<double> times;
    std::vector<double> volts;
    times.reserve(total_pts);
    volts.reserve(total_pts);

    int half_spb = samples_per_bit_ / 2;
    double dt = bit_duration_ / samples_per_bit_;

    for (int i = 0; i < n; ++i) {
        auto [v1, v2] = bit_to_half_voltages(bits[i]);
        for (int s = 0; s < samples_per_bit_; ++s) {
            times.push_back((i * samples_per_bit_ + s) * dt);
            volts.push_back(s < half_spb ? v1 : v2);
        }
    }

    SignalWaveform wf;
    wf.bits = bits;
    wf.time_points = std::move(times);
    wf.voltages = std::move(volts);
    wf.samples_per_bit = samples_per_bit_;
    wf.bit_duration = bit_duration_;
    wf.positive_voltage = positive_voltage_;
    wf.negative_voltage = negative_voltage_;
    wf.zero_voltage = zero_voltage_;
    wf.metadata["scheme"] = "Manchester";
    wf.metadata["convention"] = convention_ == ManchesterConvention::IEEE ? "ieee" : "thomas";
    return wf;
}

std::string ManchesterEncoder::decode(const SignalWaveform& waveform) {
    int spb = waveform.samples_per_bit;
    int q1 = spb / 4;
    int q3 = (3 * spb) / 4;
    double threshold = (positive_voltage_ + negative_voltage_) / 2.0;

    std::string recovered;
    recovered.reserve(waveform.num_bits());

    for (int i = 0; i < waveform.num_bits(); ++i) {
        int idx1 = i * spb + q1;
        int idx2 = i * spb + q3;
        double v1 = waveform.voltages[idx1];
        double v2 = waveform.voltages[idx2];

        bool first_high = (v1 >= threshold);
        bool second_high = (v2 >= threshold);

        if (convention_ == ManchesterConvention::IEEE) {
            recovered.push_back((first_high && !second_high) ? '0' : '1');
        } else {
            recovered.push_back((!first_high && second_high) ? '0' : '1');
        }
    }
    return recovered;
}

// -------------------------------------------------------------
// Differential Manchester
// -------------------------------------------------------------
DifferentialManchesterEncoder::DifferentialManchesterEncoder(
    double initial_voltage,
    int samples_per_bit,
    double bit_duration,
    double positive_voltage,
    double negative_voltage
) : LineEncoder(samples_per_bit, bit_duration, positive_voltage, negative_voltage, 0.0),
    initial_voltage_(initial_voltage) {}

SignalWaveform DifferentialManchesterEncoder::encode(const std::string& bits) {
    validate_input(bits);
    int n = static_cast<int>(bits.size());
    int total_pts = n * samples_per_bit_;
    std::vector<double> times;
    std::vector<double> volts;
    times.reserve(total_pts);
    volts.reserve(total_pts);

    int half_spb = samples_per_bit_ / 2;
    double dt = bit_duration_ / samples_per_bit_;
    double current_level = initial_voltage_;

    for (int i = 0; i < n; ++i) {
        char bit = bits[i];
        if (bit == '0') {
            current_level = (std::abs(current_level - positive_voltage_) < 1e-6) ? negative_voltage_ : positive_voltage_;
        }
        double first_half = current_level;
        double second_half = (std::abs(first_half - positive_voltage_) < 1e-6) ? negative_voltage_ : positive_voltage_;
        current_level = second_half;

        for (int s = 0; s < samples_per_bit_; ++s) {
            times.push_back((i * samples_per_bit_ + s) * dt);
            volts.push_back(s < half_spb ? first_half : second_half);
        }
    }

    SignalWaveform wf;
    wf.bits = bits;
    wf.time_points = std::move(times);
    wf.voltages = std::move(volts);
    wf.samples_per_bit = samples_per_bit_;
    wf.bit_duration = bit_duration_;
    wf.positive_voltage = positive_voltage_;
    wf.negative_voltage = negative_voltage_;
    wf.zero_voltage = zero_voltage_;
    wf.metadata["scheme"] = "Differential Manchester";
    return wf;
}

std::string DifferentialManchesterEncoder::decode(const SignalWaveform& waveform) {
    int spb = waveform.samples_per_bit;
    int q1 = spb / 4;
    double threshold = (positive_voltage_ + negative_voltage_) / 2.0;
    double last_half = initial_voltage_;

    std::string recovered;
    recovered.reserve(waveform.num_bits());

    for (int i = 0; i < waveform.num_bits(); ++i) {
        int idx1 = i * spb + q1;
        double v1 = waveform.voltages[idx1];

        bool current_first_high = (v1 >= threshold);
        bool last_second_high = (last_half >= threshold);

        if (current_first_high != last_second_high) {
            recovered.push_back('0');
        } else {
            recovered.push_back('1');
        }
        int idx2 = i * spb + (3 * spb) / 4;
        last_half = waveform.voltages[idx2];
    }
    return recovered;
}

// -------------------------------------------------------------
// AMI (Bipolar Alternating Mark Inversion)
// -------------------------------------------------------------
AMIEncoder::AMIEncoder(
    std::optional<double> initial_polarity,
    int samples_per_bit,
    double bit_duration,
    double positive_voltage,
    double negative_voltage,
    double zero_voltage
) : LineEncoder(samples_per_bit, bit_duration, positive_voltage, negative_voltage, zero_voltage),
    initial_polarity_(initial_polarity) {}

SignalWaveform AMIEncoder::encode(const std::string& bits) {
    validate_input(bits);
    int n = static_cast<int>(bits.size());
    int total_pts = n * samples_per_bit_;
    std::vector<double> times;
    std::vector<double> volts;
    times.reserve(total_pts);
    volts.reserve(total_pts);

    double dt = bit_duration_ / samples_per_bit_;
    double last_polarity = initial_polarity_.value_or(negative_voltage_);

    for (int i = 0; i < n; ++i) {
        char bit = bits[i];
        double level = zero_voltage_;
        if (bit == '1') {
            level = (std::abs(last_polarity - positive_voltage_) < 1e-6) ? negative_voltage_ : positive_voltage_;
            last_polarity = level;
        }
        for (int s = 0; s < samples_per_bit_; ++s) {
            times.push_back((i * samples_per_bit_ + s) * dt);
            volts.push_back(level);
        }
    }

    SignalWaveform wf;
    wf.bits = bits;
    wf.time_points = std::move(times);
    wf.voltages = std::move(volts);
    wf.samples_per_bit = samples_per_bit_;
    wf.bit_duration = bit_duration_;
    wf.positive_voltage = positive_voltage_;
    wf.negative_voltage = negative_voltage_;
    wf.zero_voltage = zero_voltage_;
    wf.metadata["scheme"] = "AMI";
    return wf;
}

std::string AMIEncoder::decode(const SignalWaveform& waveform) {
    double threshold = std::min(std::abs(positive_voltage_), std::abs(negative_voltage_)) * 0.5;
    std::string recovered;
    recovered.reserve(waveform.num_bits());

    for (int i = 0; i < waveform.num_bits(); ++i) {
        auto [t, v] = waveform.get_midpoint_sample(i);
        if (std::abs(v) > threshold) {
            recovered.push_back('1');
        } else {
            recovered.push_back('0');
        }
    }
    return recovered;
}

} // namespace line_coding
} // namespace dc
