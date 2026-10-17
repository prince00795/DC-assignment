#pragma once

#include "analog/continuous_signal.hpp"
#include "analog/sampling.hpp"
#include "line_coding/base.hpp"
#include <string>
#include <vector>

namespace dc {
namespace analog {

class WaveformPlotter {
public:
    static std::string plot_ascii_waveform(
        const std::vector<double>& times,
        const std::vector<double>& values,
        int width = 70,
        int height = 15,
        const std::string& title = ""
    );

    static std::string plot_multi_track_ascii(
        const std::vector<std::string>& track_names,
        const std::vector<std::vector<double>>& track_values,
        int width = 70,
        int height_per_track = 6
    );

    static void export_svg(
        const std::string& filepath,
        const std::vector<std::string>& track_names,
        const std::vector<std::vector<double>>& track_times,
        const std::vector<std::vector<double>>& track_values,
        int width = 1000,
        int height = 800
    );

    static void export_html_dashboard(
        const std::string& filepath,
        const std::string& title,
        const std::vector<std::string>& track_names,
        const std::vector<std::vector<double>>& track_times,
        const std::vector<std::vector<double>>& track_values,
        const std::vector<std::string>& track_colors = {}
    );
};

} // namespace analog
} // namespace dc
