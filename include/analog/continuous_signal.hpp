#pragma once

#include <vector>
#include <string>
#include <utility>

namespace dc {
namespace analog {

struct ToneComponent {
    double amplitude = 1.0;
    double frequency = 1.0;  // Hz
    double phase = 0.0;      // radians
    double dc_offset = 0.0;  // Volts
};

class ContinuousSignal {
public:
    ContinuousSignal() = default;
    explicit ContinuousSignal(std::vector<ToneComponent> tones);

    double evaluate(double t) const;
    double max_frequency() const;
    double nyquist_rate() const;

    std::pair<std::vector<double>, std::vector<double>> generate_continuous_waveform(
        double duration = 1.0,
        int points_per_cycle = 50
    ) const;

    std::pair<std::vector<double>, std::vector<double>> sample(
        double sampling_rate,
        double duration = 1.0
    ) const;

    double rms_voltage(double duration = 1.0, int points = 1000) const;
    double average_power(double duration = 1.0, int points = 1000) const;
    double papr_db(double duration = 1.0, int points = 1000) const;

    const std::vector<ToneComponent>& tones() const { return tones_; }

    static ContinuousSignal create_simple_sine(
        double amplitude = 1.0,
        double frequency = 1.0,
        double phase = 0.0,
        double dc_offset = 0.0
    );

    static ContinuousSignal create_dual_tone(
        double a1 = 1.0, double f1 = 1.0,
        double a2 = 0.5, double f2 = 3.0
    );

    static ContinuousSignal create_harmonic_series(
        const std::string& type = "square",
        double fundamental_freq = 1.0,
        int harmonics = 5,
        double base_amplitude = 1.0
    );

private:
    std::vector<ToneComponent> tones_;
};

} // namespace analog
} // namespace dc
