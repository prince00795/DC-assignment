#pragma once

#include "analog/continuous_signal.hpp"
#include <vector>
#include <string>
#include <utility>

namespace dc {
namespace analog {

struct SamplingResult {
    std::vector<double> sample_times;
    std::vector<double> sample_values;
    double sampling_rate = 1.0;
    double nyquist_rate = 1.0;
    bool is_nyquist_satisfied = true;
    double oversampling_ratio = 1.0;
    std::string mode = "ideal";
    std::vector<double> zoh_times;
    std::vector<double> zoh_values;
    std::vector<std::pair<double, double>> apparent_frequencies;

    std::vector<double> reconstruct_sinc(const std::vector<double>& eval_times) const;
    std::pair<double, double> compute_reconstruction_metrics(
        const ContinuousSignal& signal,
        double duration = 1.0,
        int num_eval_points = 400,
        double margin = 0.1
    ) const;
};

class NyquistSampler {
public:
    NyquistSampler() = default;

    SamplingResult sample(
        const ContinuousSignal& signal,
        double sampling_rate,
        double duration = 1.0,
        const std::string& mode = "ideal",
        double pulse_width = 0.0,
        int points_per_pulse = 10
    );

    SamplingResult sample_at_nyquist(
        const ContinuousSignal& signal,
        double duration = 1.0,
        double multiplier = 1.0
    );
};

} // namespace analog
} // namespace dc
