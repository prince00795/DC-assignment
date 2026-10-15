#include "analog/delta_modulation.hpp"
#include <cmath>
#include <stdexcept>

namespace dc {
namespace analog {

constexpr double PI = 3.14159265358979323846;

DeltaModulator::DeltaModulator(
    double step_size,
    double sampling_rate,
    double initial_value
) : step_size_(step_size),
    sampling_rate_(sampling_rate),
    initial_value_(initial_value) {
    if (step_size <= 0.0) {
        throw std::invalid_argument("step_size must be positive, got " + std::to_string(step_size));
    }
    if (sampling_rate <= 0.0) {
        throw std::invalid_argument("sampling_rate must be positive, got " + std::to_string(sampling_rate));
    }
}

DeltaModulationResult DeltaModulator::encode_samples(
    const std::vector<double>& samples,
    const std::vector<double>& times
) const {
    DeltaModulationResult res;
    res.step_size = step_size_;
    res.sampling_rate = sampling_rate_;
    res.original_samples = samples;

    int n = static_cast<int>(samples.size());
    if (n == 0) return res;

    if (!times.empty() && static_cast<int>(times.size()) == n) {
        res.time_points = times;
    } else {
        res.time_points.reserve(n);
        double dt = 1.0 / sampling_rate_;
        for (int i = 0; i < n; ++i) {
            res.time_points.push_back(i * dt);
        }
    }

    res.staircase_samples.reserve(n);
    res.bitstream.reserve(n);

    double x_hat = initial_value_;
    double dt = 1.0 / sampling_rate_;
    double tracking_limit = step_size_ * sampling_rate_;

    double total_err_sq = 0.0;
    double total_sig_sq = 0.0;

    for (int i = 0; i < n; ++i) {
        double x = samples[i];
        if (x >= x_hat) {
            res.bitstream.push_back('1');
            x_hat += step_size_;
        } else {
            res.bitstream.push_back('0');
            x_hat -= step_size_;
        }
        res.staircase_samples.push_back(x_hat);

        double err = x - x_hat;
        total_err_sq += err * err;
        total_sig_sq += x * x;

        // Slope overload check
        if (i > 0) {
            double actual_slope = std::abs(samples[i] - samples[i - 1]) / dt;
            if (actual_slope > tracking_limit + 1e-6) {
                res.slope_overload_indices.push_back(i);
            }
        }
    }

    // Granular noise detection (hunting alternating pattern)
    if (n >= 4) {
        for (int i = 0; i <= n - 4; ++i) {
            std::string sub = res.bitstream.substr(i, 4);
            if (sub == "1010" || sub == "0101") {
                double min_v = samples[i];
                double max_v = samples[i];
                for (int k = 1; k < 4; ++k) {
                    if (samples[i + k] < min_v) min_v = samples[i + k];
                    if (samples[i + k] > max_v) max_v = samples[i + k];
                }
                if ((max_v - min_v) <= 1.5 * step_size_) {
                    res.granular_noise_indices.push_back(i);
                }
            }
        }
    }

    res.mse = total_err_sq / n;
    double sig_pow = total_sig_sq / n;
    if (res.mse > 1e-12 && sig_pow > 1e-12) {
        res.snr_db = 10.0 * std::log10(sig_pow / res.mse);
    } else {
        res.snr_db = (sig_pow <= 1e-12) ? 0.0 : 100.0;
    }

    return res;
}

std::vector<double> DeltaModulator::decode_bitstream(const std::string& bitstream) const {
    std::vector<double> recovered;
    recovered.reserve(bitstream.size());

    double x_hat = initial_value_;
    for (char b : bitstream) {
        if (b == '1') {
            x_hat += step_size_;
        } else if (b == '0') {
            x_hat -= step_size_;
        } else {
            throw std::invalid_argument(std::string("Invalid bit '") + b + "', expected '0' or '1'.");
        }
        recovered.push_back(x_hat);
    }
    return recovered;
}

bool DeltaModulator::check_slope_overload(
    const ContinuousSignal& signal,
    double& max_signal_slope,
    double& tracking_slope
) const {
    max_signal_slope = 0.0;
    for (const auto& tone : signal.tones()) {
        max_signal_slope += 2.0 * PI * tone.frequency * tone.amplitude;
    }
    tracking_slope = max_tracking_slope();
    return tracking_slope >= max_signal_slope;
}

} // namespace analog
} // namespace dc
