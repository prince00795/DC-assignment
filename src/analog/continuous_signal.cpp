#include "analog/continuous_signal.hpp"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>

namespace dc {
namespace analog {

constexpr double PI = 3.14159265358979323846;

ContinuousSignal::ContinuousSignal(std::vector<ToneComponent> tones)
    : tones_(std::move(tones)) {}

double ContinuousSignal::evaluate(double t) const {
    double total = 0.0;
    for (const auto& tone : tones_) {
        total += tone.amplitude * std::sin(2.0 * PI * tone.frequency * t + tone.phase) + tone.dc_offset;
    }
    return total;
}

double ContinuousSignal::max_frequency() const {
    if (tones_.empty()) return 1.0;
    double max_f = 0.0;
    for (const auto& tone : tones_) {
        if (tone.frequency > max_f) max_f = tone.frequency;
    }
    return max_f > 0.0 ? max_f : 1.0;
}

double ContinuousSignal::nyquist_rate() const {
    return 2.0 * max_frequency();
}

std::pair<std::vector<double>, std::vector<double>> ContinuousSignal::generate_continuous_waveform(
    double duration,
    int points_per_cycle
) const {
    if (duration <= 0.0) {
        throw std::invalid_argument("Duration must be positive");
    }
    double f_max = max_frequency();
    double dt = 1.0 / (points_per_cycle * f_max);
    int total_pts = static_cast<int>(std::ceil(duration / dt)) + 1;

    std::vector<double> t_pts;
    std::vector<double> v_pts;
    t_pts.reserve(total_pts);
    v_pts.reserve(total_pts);

    for (int i = 0; i < total_pts; ++i) {
        double t = i * dt;
        if (t > duration + 1e-9) break;
        t_pts.push_back(t);
        v_pts.push_back(evaluate(t));
    }
    return {t_pts, v_pts};
}

std::pair<std::vector<double>, std::vector<double>> ContinuousSignal::sample(
    double sampling_rate,
    double duration
) const {
    if (sampling_rate <= 0.0 || duration <= 0.0) {
        throw std::invalid_argument("sampling_rate and duration must be positive");
    }
    double dt = 1.0 / sampling_rate;
    int total_pts = static_cast<int>(std::ceil(duration * sampling_rate));

    std::vector<double> t_pts;
    std::vector<double> v_pts;
    t_pts.reserve(total_pts);
    v_pts.reserve(total_pts);

    for (int i = 0; i < total_pts; ++i) {
        double t = i * dt;
        if (t > duration + 1e-9) break;
        t_pts.push_back(t);
        v_pts.push_back(evaluate(t));
    }
    return {t_pts, v_pts};
}

double ContinuousSignal::rms_voltage(double duration, int points) const {
    if (points <= 1 || duration <= 0.0) return 0.0;
    double dt = duration / (points - 1);
    double sum_sq = 0.0;
    for (int i = 0; i < points; ++i) {
        double v = evaluate(i * dt);
        sum_sq += v * v;
    }
    return std::sqrt(sum_sq / points);
}

double ContinuousSignal::average_power(double duration, int points) const {
    double rms = rms_voltage(duration, points);
    return rms * rms;
}

double ContinuousSignal::papr_db(double duration, int points) const {
    double p_avg = average_power(duration, points);
    if (p_avg <= 1e-12) return 0.0;

    double dt = duration / (points - 1);
    double max_sq = 0.0;
    for (int i = 0; i < points; ++i) {
        double v = evaluate(i * dt);
        double sq = v * v;
        if (sq > max_sq) max_sq = sq;
    }
    return 10.0 * std::log10(max_sq / p_avg);
}

ContinuousSignal ContinuousSignal::create_simple_sine(
    double amplitude,
    double frequency,
    double phase,
    double dc_offset
) {
    return ContinuousSignal({ToneComponent{amplitude, frequency, phase, dc_offset}});
}

ContinuousSignal ContinuousSignal::create_dual_tone(
    double a1, double f1,
    double a2, double f2
) {
    return ContinuousSignal({
        ToneComponent{a1, f1, 0.0, 0.0},
        ToneComponent{a2, f2, 0.0, 0.0}
    });
}

ContinuousSignal ContinuousSignal::create_harmonic_series(
    const std::string& type,
    double fundamental_freq,
    int harmonics,
    double base_amplitude
) {
    std::vector<ToneComponent> tones;
    if (type == "sawtooth") {
        for (int k = 1; k <= harmonics; ++k) {
            double amp = base_amplitude * (2.0 / (k * PI)) * ((k % 2 == 1) ? 1.0 : -1.0);
            tones.push_back(ToneComponent{amp, fundamental_freq * k, 0.0, 0.0});
        }
    } else { // "square"
        for (int k = 1; k <= harmonics; ++k) {
            int n = 2 * k - 1; // odd harmonics
            double amp = base_amplitude * (4.0 / (n * PI));
            tones.push_back(ToneComponent{amp, fundamental_freq * n, 0.0, 0.0});
        }
    }
    return ContinuousSignal(tones);
}

} // namespace analog
} // namespace dc
