#include "analog/plotter.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <algorithm>

namespace dc {
namespace analog {

std::string WaveformPlotter::plot_ascii_waveform(
    const std::vector<double>& times,
    const std::vector<double>& values,
    int width,
    int height,
    const std::string& title
) {
    if (values.empty()) return "[Empty Waveform]";

    double v_min = *std::min_element(values.begin(), values.end());
    double v_max = *std::max_element(values.begin(), values.end());
    if (std::abs(v_max - v_min) < 1e-6) {
        v_max += 1.0;
        v_min -= 1.0;
    }

    std::vector<std::string> grid(height, std::string(width, ' '));

    // Zero-axis line if in range
    int zero_row = -1;
    if (v_min <= 0.0 && v_max >= 0.0) {
        zero_row = static_cast<int>((v_max - 0.0) / (v_max - v_min) * (height - 1));
        if (zero_row >= 0 && zero_row < height) {
            for (int col = 0; col < width; ++col) {
                grid[zero_row][col] = '-';
            }
        }
    }

    size_t n = values.size();
    for (int col = 0; col < width; ++col) {
        size_t idx = (col * n) / width;
        if (idx >= n) idx = n - 1;
        double val = values[idx];
        int row = static_cast<int>((v_max - val) / (v_max - v_min) * (height - 1));
        row = std::clamp(row, 0, height - 1);
        grid[row][col] = '*';
    }

    std::ostringstream oss;
    if (!title.empty()) {
        oss << "=== " << title << " ===\n";
    }
    for (int r = 0; r < height; ++r) {
        double row_val = v_max - (r * (v_max - v_min) / (height - 1));
        oss << std::setw(6) << std::fixed << std::setprecision(2) << row_val << " |";
        oss << grid[r] << "|\n";
    }
    oss << "       +" << std::string(width, '-') << "+\n";
    if (!times.empty()) {
        oss << "       0.0s" << std::string(width - 10, ' ') << std::fixed << std::setprecision(2) << times.back() << "s\n";
    }
    return oss.str();
}

std::string WaveformPlotter::plot_multi_track_ascii(
    const std::vector<std::string>& track_names,
    const std::vector<std::vector<double>>& track_values,
    int width,
    int height_per_track
) {
    std::ostringstream oss;
    for (size_t t = 0; t < track_names.size() && t < track_values.size(); ++t) {
        oss << "[" << track_names[t] << "]\n";
        oss << plot_ascii_waveform({}, track_values[t], width, height_per_track, "");
        oss << "\n";
    }
    return oss.str();
}

void WaveformPlotter::export_svg(
    const std::string& filepath,
    const std::vector<std::string>& track_names,
    const std::vector<std::vector<double>>& track_times,
    const std::vector<std::vector<double>>& track_values,
    int width,
    int height
) {
    (void)track_times;
    std::ofstream out(filepath);
    if (!out.is_open()) return;

    size_t num_tracks = std::min(track_names.size(), track_values.size());
    if (num_tracks == 0) return;

    int track_height = (height - 80) / static_cast<int>(num_tracks);

    out << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
    out << "<svg width=\"" << width << "\" height=\"" << height << "\" xmlns=\"http://www.w3.org/2000/svg\">\n";
    out << "<rect width=\"100%\" height=\"100%\" fill=\"#1e1e2e\"/>\n";
    out << "<text x=\"30\" y=\"35\" font-family=\"sans-serif\" font-size=\"20\" font-weight=\"bold\" fill=\"#cdd6f4\">Digital Signal & Modulation Dashboard</text>\n";

    std::vector<std::string> colors = {"#89b4fa", "#a6e3a1", "#fab387", "#f38ba8", "#cba6f7", "#94e2d5"};

    for (size_t t = 0; t < num_tracks; ++t) {
        int y_top = 60 + static_cast<int>(t) * track_height;
        int y_mid = y_top + track_height / 2;
        int plot_width = width - 120;
        int x_left = 80;

        // Track frame
        out << "<rect x=\"" << x_left << "\" y=\"" << y_top << "\" width=\"" << plot_width << "\" height=\"" << (track_height - 15) << "\" fill=\"#181825\" stroke=\"#313244\"/>\n";
        out << "<line x1=\"" << x_left << "\" y1=\"" << y_mid << "\" x2=\"" << (x_left + plot_width) << "\" y2=\"" << y_mid << "\" stroke=\"#45475a\" stroke-dasharray=\"4\"/>\n";
        out << "<text x=\"10\" y=\"" << (y_mid + 5) << "\" font-family=\"sans-serif\" font-size=\"12\" fill=\"#a6adc8\">Track " << (t + 1) << "</text>\n";
        out << "<text x=\"" << (x_left + 10) << "\" y=\"" << (y_top + 18) << "\" font-family=\"sans-serif\" font-size=\"13\" font-weight=\"bold\" fill=\"" << colors[t % colors.size()] << "\">" << track_names[t] << "</text>\n";

        const auto& vals = track_values[t];
        if (vals.size() > 1) {
            double v_min = *std::min_element(vals.begin(), vals.end());
            double v_max = *std::max_element(vals.begin(), vals.end());
            if (std::abs(v_max - v_min) < 1e-6) {
                v_max += 1.0;
                v_min -= 1.0;
            }

            std::ostringstream path;
            for (size_t i = 0; i < vals.size(); ++i) {
                double norm_x = static_cast<double>(i) / (vals.size() - 1);
                double norm_y = (v_max - vals[i]) / (v_max - v_min);
                int px = x_left + static_cast<int>(norm_x * plot_width);
                int py = y_top + static_cast<int>(norm_y * (track_height - 25)) + 5;
                if (i == 0) path << "M " << px << " " << py;
                else path << " L " << px << " " << py;
            }
            out << "<path d=\"" << path.str() << "\" fill=\"none\" stroke=\"" << colors[t % colors.size()] << "\" stroke-width=\"2\"/>\n";
        }
    }

    out << "</svg>\n";
}

void WaveformPlotter::export_html_dashboard(
    const std::string& filepath,
    const std::string& title,
    const std::vector<std::string>& track_names,
    const std::vector<std::vector<double>>& track_times,
    const std::vector<std::vector<double>>& track_values,
    const std::vector<std::string>& track_colors
) {
    (void)track_colors;
    std::string svg_path = filepath + ".svg";
    export_svg(svg_path, track_names, track_times, track_values, 1200, 900);

    std::ofstream out(filepath);
    if (!out.is_open()) return;

    out << "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n";
    out << "<meta charset=\"UTF-8\">\n<title>" << title << "</title>\n";
    out << "<style>\n";
    out << "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f111a; color: #e6edf3; padding: 24px; }\n";
    out << ".card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); max-width: 1250px; margin: auto; }\n";
    out << "h1 { color: #58a6ff; margin-bottom: 8px; }\n";
    out << ".meta { color: #8b949e; font-size: 14px; margin-bottom: 20px; }\n";
    out << "img { width: 100%; border-radius: 6px; border: 1px solid #30363d; }\n";
    out << "</style>\n</head>\n<body>\n";
    out << "<div class=\"card\">\n";
    out << "<h1>" << title << "</h1>\n";
    out << "<p class=\"meta\">ITT 036: Digital Signal Transmission & Line Coding Simulation Suite | Synchronized Waveform Dashboard</p>\n";
    out << "<img src=\"" << svg_path << "\" alt=\"Waveform SVG\"/>\n";
    out << "</div>\n</body>\n</html>\n";
}

} // namespace analog
} // namespace dc
