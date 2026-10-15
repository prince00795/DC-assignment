#pragma once

#include "analog/continuous_signal.hpp"
#include <vector>
#include <string>

namespace dc {
namespace analog {

struct DeltaModulationResult {
    std::vector<double> time_points;
    std::vector<double> original_samples;
    std::vector<double> staircase_samples;
    std::string bitstream;
    double step_size = 0.25;
    double sampling_rate = 100.0;
    std::vector<int> slope_overload_indices;
    std::vector<int> granular_noise_indices;
    double mse = 0.0;
    double snr_db = 0.0;

    int bit_count() const { return static_cast<int>(bitstream.size()); }
};

class DeltaModulator {
public:
    explicit DeltaModulator(
        double step_size = 0.25,
        double sampling_rate = 100.0,
        double initial_value = 0.0
    );

    double step_size() const { return step_size_; }
    double sampling_rate() const { return sampling_rate_; }
    double initial_value() const { return initial_value_; }
    double max_tracking_slope() const { return step_size_ * sampling_rate_; }

    DeltaModulationResult encode_samples(
        const std::vector<double>& samples,
        const std::vector<double>& times = {}
    ) const;

    std::vector<double> decode_bitstream(const std::string& bitstream) const;

    bool check_slope_overload(
        const ContinuousSignal& signal,
        double& max_signal_slope,
        double& tracking_slope
    ) const;

private:
    double step_size_;
    double sampling_rate_;
    double initial_value_;
};

} // namespace analog
} // namespace dc
