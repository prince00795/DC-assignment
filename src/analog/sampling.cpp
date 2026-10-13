#include "analog/sampling.hpp"
#include <cmath>
#include <stdexcept>
#include <algorithm>

namespace dc {
namespace analog {

constexpr double PI = 3.14159265358979323846;

static double sinc(double u) {
    if (std::abs(u) < 1e-9) return 1.0;
    double pi_u = PI * u;
    return std::sin(pi_u) / pi_u;
}

std::vector<double> SamplingResult::reconstruct_sinc(const std::vector<double>& eval_times) const {
    if (sample_times.empty()) return std::vector<double>(eval_times.size(), 0.0);

    double Ts = 1.0 / sampling_rate;
    std::vector<double> recon;
    recon.reserve(eval_times.size());

    for (double t : eval_times) {
        double val = 0.0;
        for (size_t n = 0; n < sample_times.size(); ++n) {
            double u = (t - sample_times[n]) / Ts;
            val += sample_values[n] * sinc(u);
        }
        recon.push_back(val);
    }
    return recon;
}

std::pair<double, double> SamplingResult::compute_reconstruction_metrics(
    const ContinuousSignal& signal,
    double duration,
    int num_eval_points,
    double margin
) const {
    double t_start = duration * margin;
    double t_end = duration * (1.0 - margin);
    if (t_end <= t_start) {
        t_start = 0.0;
        t_end = duration;
    }

    double dt = (t_end - t_start) / std::max(num_eval_points - 1, 1);
    std::vector<double> t_dense;
    std::vector<double> orig_dense;
    t_dense.reserve(num_eval_points);
    orig_dense.reserve(num_eval_points);

    for (int i = 0; i < num_eval_points; ++i) {
        double t = t_start + i * dt;
        t_dense.push_back(t);
        orig_dense.push_back(signal.evaluate(t));
    }

    std::vector<double> recon_dense = reconstruct_sinc(t_dense);

    double mse = 0.0;
    double signal_pow = 0.0;
    for (int i = 0; i < num_eval_points; ++i) {
        double err = orig_dense[i] - recon_dense[i];
        mse += err * err;
        signal_pow += orig_dense[i] * orig_dense[i];
    }
    mse /= num_eval_points;
    signal_pow /= num_eval_points;

    double snr_db = 100.0;
    if (mse > 1e-12 && signal_pow > 1e-12) {
        snr_db = 10.0 * std::log10(signal_pow / mse);
    } else if (signal_pow <= 1e-12) {
        snr_db = 0.0;
    }
    return {mse, snr_db};
}

SamplingResult NyquistSampler::sample(
    const ContinuousSignal& signal,
    double sampling_rate,
    double duration,
    const std::string& mode,
    double pulse_width,
    int points_per_pulse
) {
    if (sampling_rate <= 0.0 || duration <= 0.0) {
        throw std::invalid_argument("sampling_rate and duration must be positive");
    }

    double nyquist = signal.nyquist_rate();
    bool is_satisfied = (sampling_rate >= nyquist);
    double osr = sampling_rate / nyquist;

    auto [sample_times, sample_values] = signal.sample(sampling_rate, duration);

    // Compute aliased / apparent folded frequencies
    double f_N = sampling_rate / 2.0;
    std::vector<std::pair<double, double>> apparent_freqs;
    for (const auto& tone : signal.tones()) {
        double f = tone.frequency;
        if (f <= f_N) {
            apparent_freqs.emplace_back(f, f);
        } else {
            double rem = std::fmod(f, sampling_rate);
            double folded = std::min(rem, sampling_rate - rem);
            apparent_freqs.emplace_back(f, folded);
        }
    }

    SamplingResult res;
    res.sample_times = std::move(sample_times);
    res.sample_values = std::move(sample_values);
    res.sampling_rate = sampling_rate;
    res.nyquist_rate = nyquist;
    res.is_nyquist_satisfied = is_satisfied;
    res.oversampling_ratio = osr;
    res.mode = mode;
    res.apparent_frequencies = std::move(apparent_freqs);

    if (mode == "flat_top" || mode == "natural") {
        double Ts = 1.0 / sampling_rate;
        double tau = (pulse_width > 0.0) ? pulse_width : Ts;
        int ppp = (points_per_pulse > 0) ? points_per_pulse : 10;
        double dt = Ts / ppp;

        std::vector<double> zoh_t;
        std::vector<double> zoh_v;

        for (size_t k = 0; k < res.sample_times.size(); ++k) {
            double t0 = res.sample_times[k];
            double s_val = res.sample_values[k];

            for (int p = 0; p < ppp; ++p) {
                double t_curr = t0 + p * dt;
                if (t_curr > duration) break;
                zoh_t.push_back(t_curr);

                if (mode == "flat_top") {
                    if (p * dt < tau) {
                        zoh_v.push_back(s_val);
                    } else {
                        zoh_v.push_back(0.0);
                    }
                } else { // "natural"
                    if (p * dt < tau) {
                        zoh_v.push_back(signal.evaluate(t_curr));
                    } else {
                        zoh_v.push_back(0.0);
                    }
                }
            }
        }
        res.zoh_times = std::move(zoh_t);
        res.zoh_values = std::move(zoh_v);
    }

    return res;
}

SamplingResult NyquistSampler::sample_at_nyquist(
    const ContinuousSignal& signal,
    double duration,
    double multiplier
) {
    if (multiplier <= 0.0) {
        throw std::invalid_argument("multiplier must be positive");
    }
    double fs = signal.nyquist_rate() * multiplier;
    return sample(signal, fs, duration, "ideal");
}

} // namespace analog
} // namespace dc
