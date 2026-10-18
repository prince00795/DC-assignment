#include "cli/menu.hpp"
#include "algorithms/palindrome.hpp"
#include "analog/continuous_signal.hpp"
#include "analog/sampling.hpp"
#include "analog/quantization.hpp"
#include "analog/delta_modulation.hpp"
#include "analog/plotter.hpp"
#include "line_coding/encoders.hpp"
#include "scrambling/b8zs.hpp"
#include "scrambling/hdb3.hpp"
#include "decoder/signal_decoder.hpp"
#include <iostream>
#include <iomanip>
#include <limits>
#include <chrono>

namespace dc {
namespace cli {

MenuController::MenuController()
    : current_bitstream_("101100100000000100001"),
      generator_(42),
      bridge_(50, 1.0, 1.0, -1.0, 0.0) {}

void MenuController::show_help_guide() const {
    std::cout << "\n==============================================================================\n"
              << " SYSTEM HELP & ARCHITECTURAL SPECIFICATION GUIDE (C++20 Native)\n"
              << "==============================================================================\n"
              << "1. SYSTEM ARCHITECTURE & MODULAR RESPONSIBILITIES:\n"
              << "   - Algorithms: Manacher's Algorithm for strict linear O(N) palindromic bitstream search.\n"
              << "   - Generator: High-entropy pseudo-random and zero-injected digital bitstream generator.\n"
              << "   - Line Coding: NRZ-L, NRZ-I, Manchester (IEEE & Thomas), Diff Manchester, AMI.\n"
              << "   - Scrambling: B8ZS (000VB0VB) and HDB3 (000V/B00V) state machines with parity tracking.\n"
              << "   - Decoder: PhysicalSignalDecoder with transition edge and mid-bit voltage slicing.\n"
              << "   - Analog DSP: Multi-tone harmonic synthesis, Nyquist sampling, Uniform PCM, Delta Modulation.\n"
              << "   - Pipeline Bridge: Complete end-to-end transmitter-channel-receiver simulation.\n"
              << "   - Visualization: Terminal ANSI waveform dashboard and standalone HTML/SVG vector exporter.\n"
              << "==============================================================================\n\n";
}

void MenuController::menu_generator() {
    std::cout << "\n--- [1] Digital Bitstream Generator ---\n"
              << "  1. Generate Pure Random Stream\n"
              << "  2. Generate B8ZS Injected Stream (8 consecutive zeros)\n"
              << "  3. Generate HDB3 Injected Stream (4 consecutive zeros)\n"
              << "  4. Enter Custom Binary Stream\n"
              << "  5. Digitize Analog Continuous Waveform via Uniform PCM\n"
              << "  6. Digitize Analog Continuous Waveform via 1-Bit Delta Modulation (DM)\n"
              << "Selection: ";
    int choice;
    if (!(std::cin >> choice)) {
        std::cin.clear();
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
        return;
    }

    if (choice == 1) {
        current_bitstream_ = generator_.generate_random(24);
        std::cout << "Generated 24-bit random stream: " << current_bitstream_ << "\n";
    } else if (choice == 2) {
        current_bitstream_ = generator_.generate_b8zs_stream(24, 1);
        std::cout << "Generated 24-bit B8ZS stream (8 zeros): " << current_bitstream_ << "\n";
    } else if (choice == 3) {
        current_bitstream_ = generator_.generate_hdb3_stream(20, 1);
        std::cout << "Generated 20-bit HDB3 stream (4 zeros): " << current_bitstream_ << "\n";
    } else if (choice == 4) {
        std::cout << "Enter binary string: ";
        std::string custom;
        std::cin >> custom;
        if (generator::DataGenerator::validate_stream(custom)) {
            current_bitstream_ = custom;
            std::cout << "Active bitstream set (" << current_bitstream_.size() << " bits): " << current_bitstream_ << "\n";
        } else {
            std::cout << "Invalid binary stream! Keeping existing stream.\n";
        }
    } else if (choice == 5) {
        auto sig = analog::ContinuousSignal::create_simple_sine(2.0, 2.0);
        analog::NyquistSampler sampler;
        auto s_res = sampler.sample(sig, 20.0, 1.0);
        analog::UniformQuantizer pcm(3, -2.5, 2.5, "natural");
        auto q_res = pcm.quantize_samples(s_res.sample_values);
        current_bitstream_ = q_res.bitstream;
        std::cout << "[Analog PCM] Generated " << current_bitstream_.size() << " bits from 20 samples (3-bit).\n";
    } else if (choice == 6) {
        auto sig = analog::ContinuousSignal::create_simple_sine(1.5, 2.0);
        auto [t_pts, v_pts] = sig.sample(25.0, 1.0);
        analog::DeltaModulator dm(0.25, 25.0, 0.0);
        auto dm_res = dm.encode_samples(v_pts, t_pts);
        current_bitstream_ = dm_res.bitstream;
        std::cout << "[Delta Modulation] Generated " << current_bitstream_.size() << " bits via 1-bit staircase tracking.\n";
    }
}

void MenuController::menu_palindrome() {
    std::cout << "\n--- [2] Manacher's O(N) Palindromic Bitstream Analysis ---\n"
              << "Target Bitstream: " << current_bitstream_ << " (Length=" << current_bitstream_.size() << ")\n";

    auto t0 = std::chrono::high_resolution_clock::now();
    algorithms::ManachersAlgorithm manacher(current_bitstream_);
    auto res = manacher.find_longest();
    auto t1 = std::chrono::high_resolution_clock::now();
    double manacher_us = std::chrono::duration<double, std::micro>(t1 - t0).count();

    auto t2 = std::chrono::high_resolution_clock::now();
    auto naive_res = algorithms::naive_longest_palindrome(current_bitstream_);
    auto t3 = std::chrono::high_resolution_clock::now();
    double naive_us = std::chrono::duration<double, std::micro>(t3 - t2).count();

    std::cout << "  Longest Palindrome:       \"" << res.substring << "\"\n"
              << "  Span:                     [" << res.start << " : " << res.end << "]\n"
              << "  Length:                   " << res.length << "\n"
              << "  Center:                   " << std::fixed << std::setprecision(1) << res.center_index << "\n"
              << "  Parity:                   " << (res.is_even ? "Even-length" : "Odd-length") << "\n"
              << "  Manacher Time:            " << std::fixed << std::setprecision(2) << manacher_us << " us (Strict O(N))\n"
              << "  Naive Time:               " << std::fixed << std::setprecision(2) << naive_us << " us (O(N^2))\n";

    auto all_palindromes = manacher.find_all(2, true);
    std::cout << "  Unique Sub-palindromes:   " << all_palindromes.size() << " found\n";
}

void MenuController::menu_line_coding() {
    std::cout << "\n--- [3] Baseband Line Coding ---\n"
              << "Active Bitstream: " << current_bitstream_ << "\n"
              << "  1. NRZ-L (Non-Return-to-Zero-Level)\n"
              << "  2. NRZ-I (Non-Return-to-Zero-Inverted)\n"
              << "  3. Manchester (IEEE 802.3)\n"
              << "  4. Differential Manchester\n"
              << "  5. AMI (Bipolar Alternating Mark Inversion)\n"
              << "Selection: ";
    int choice;
    if (!(std::cin >> choice)) return;

    std::string scheme = "NRZ-L";
    if (choice == 2) scheme = "NRZ-I";
    else if (choice == 3) scheme = "Manchester";
    else if (choice == 4) scheme = "Differential Manchester";
    else if (choice == 5) scheme = "AMI";

    auto res = bridge_.run_bitstream_pipeline(current_bitstream_, scheme, "None");
    std::cout << "\n-> Encoded " << scheme << " Waveform:\n"
              << "   Bits:              " << res.bitstream << "\n"
              << "   Total Samples:     " << res.encoded_waveform.total_samples() << " (50 samples/bit)\n"
              << "   Decoded Bits:      " << res.decoded_signal.recovered_bits << "\n"
              << "   Accuracy:          " << res.accuracy_pct << "%\n"
              << "   BER:               " << res.ber << "\n";

    std::cout << "\nWaveform Preview:\n"
              << analog::WaveformPlotter::plot_ascii_waveform({}, res.encoded_waveform.voltages, 65, 8, scheme);
}

void MenuController::menu_scrambling() {
    std::cout << "\n--- [4] Scrambling State Machines: B8ZS & HDB3 ---\n"
              << "Active Bitstream: " << current_bitstream_ << "\n"
              << "  1. B8ZS (North American T1 8-Zero Substitution: 000VB0VB)\n"
              << "  2. HDB3 (European E1 4-Zero Substitution: 000V / B00V)\n"
              << "Selection: ";
    int choice;
    if (!(std::cin >> choice)) return;

    std::string scramble = (choice == 1) ? "B8ZS" : "HDB3";
    auto res = bridge_.run_bitstream_pipeline(current_bitstream_, "AMI", scramble);

    std::cout << "\n-> Scrambled AMI (" << scramble << ") Analysis:\n"
              << "   Original Bits:     " << res.bitstream << "\n"
              << "   Violations Found:  " << res.scrambled_waveform->violation_indices.size() << " at positions [";
    for (size_t i = 0; i < res.scrambled_waveform->violation_indices.size(); ++i) {
        std::cout << res.scrambled_waveform->violation_indices[i] << (i + 1 < res.scrambled_waveform->violation_indices.size() ? ", " : "");
    }
    std::cout << "]\n"
              << "   Bipolar Markers:   " << res.scrambled_waveform->bipolar_indices.size() << "\n"
              << "   Decoded Bits:      " << res.decoded_signal.recovered_bits << "\n"
              << "   Recovery:          " << (res.verification_passed ? "100% MATCH" : "MISMATCH") << "\n";
}

void MenuController::menu_analog_pcm() {
    std::cout << "\n--- [5] Analog Modulation: Continuous Wave & Uniform PCM ---\n";
    auto sig = analog::ContinuousSignal::create_dual_tone(2.0, 1.0, 1.0, 3.0);
    double nyquist = sig.nyquist_rate();
    std::cout << "Signal: Dual-Tone (2.0V @ 1Hz + 1.0V @ 3Hz), Nyquist Rate = " << nyquist << " Hz\n";

    analog::NyquistSampler sampler;
    auto s_res = sampler.sample(sig, 12.0, 1.0, "flat_top");
    std::cout << "Sampled at fs = 12.0 Hz (" << s_res.oversampling_ratio << "x Nyquist)\n";

    analog::UniformQuantizer pcm(3, -3.5, 3.5, "natural");
    auto q_res = pcm.quantize_samples(s_res.sample_values);

    std::cout << "Quantized with n = 3 bits (8 levels, Delta = " << q_res.step_size << " V):\n"
              << "  Theoretical SQNR: " << q_res.theoretical_sqnr_db << " dB\n"
              << "  Empirical SQNR:   " << q_res.empirical_sqnr_db << " dB\n"
              << "  MSE Distortion:   " << q_res.mse << "\n"
              << "  Resulting Bits:   " << q_res.bitstream << "\n";
}

void MenuController::menu_delta_modulation() {
    std::cout << "\n--- [6] Delta Modulation (DM): 1-Bit Tracking & Diagnostics ---\n";
    auto sig = analog::ContinuousSignal::create_simple_sine(2.0, 2.0);
    double max_slope = 0.0, track_slope = 0.0;
    analog::DeltaModulator dm(0.20, 40.0, 0.0);
    bool avoids_overload = dm.check_slope_overload(sig, max_slope, track_slope);

    std::cout << "Continuous Sine: A=2.0V, f=2.0Hz | Max |dx/dt| = " << max_slope << " V/s\n"
              << "DM Parameters:   Delta=0.20V, fs=40.0Hz | Tracking Limit = " << track_slope << " V/s\n"
              << "Slope Overload:  " << (avoids_overload ? "AVOIDED (Linear tracking guaranteed)" : "OCCURS (Distortion detected)") << "\n";

    auto [times, samples] = sig.sample(40.0, 1.0);
    auto dm_res = dm.encode_samples(samples, times);
    std::cout << "Encoded 40 bits: " << dm_res.bitstream << "\n"
              << "Overload count:  " << dm_res.slope_overload_indices.size() << "\n"
              << "Granular noise:  " << dm_res.granular_noise_indices.size() << "\n";
}

void MenuController::menu_pipeline() {
    std::cout << "\n--- [7] Full End-to-End Integrated Transmission Pipeline ---\n";
    auto sig = analog::ContinuousSignal::create_simple_sine(1.5, 2.0);
    auto res = bridge_.run_analog_to_line_coding(sig, 20.0, 1.0, "PCM", 3, 0.25, "AMI", "B8ZS");

    std::cout << "Pipeline Execution Outcome:\n"
              << "  Analog Input:        1.5V Sine @ 2.0 Hz\n"
              << "  PCM Quantization:    3-bit Natural binary -> " << res.bitstream.size() << " bits\n"
              << "  Line Coding:         AMI with B8ZS Scrambling\n"
              << "  Physical Samples:    " << res.encoded_waveform.total_samples() << " points\n"
              << "  Decoded Bitstream:   " << res.decoded_signal.recovered_bits << "\n"
              << "  Bit Error Rate:      " << res.ber << " (Accuracy = " << res.accuracy_pct << "%)\n"
              << "  Verification Status: " << (res.verification_passed ? "PASSED (Zero transmission error)" : "FAILED") << "\n";

    // Export SVG & HTML dashboard snapshot
    std::vector<std::string> names = {"[Track 1] Analog Source", "[Track 2] Reconstructed Staircase", "[Track 3] B8ZS AMI Waveform"};
    std::vector<std::vector<double>> tracks = {
        res.analog_signal.generate_continuous_waveform(1.0, 25).second,
        res.sampling_result.zoh_values.empty() ? res.sampling_result.sample_values : res.sampling_result.zoh_values,
        res.scrambled_waveform->voltages
    };
    analog::WaveformPlotter::export_html_dashboard("waveform_dashboard.html", "Digital Communication Pipeline Dashboard", names, {}, tracks);
    std::cout << "\n[Dashboard Export] High-resolution HTML/SVG visualizer exported to: 'waveform_dashboard.html'\n";
}

void MenuController::run_interactive() {
    while (true) {
        std::cout << "\n==============================================================================\n"
                  << " ITT 036: DIGITAL SIGNAL TRANSMISSION, MODULATION & LINE CODING SYSTEM (C++20)\n"
                  << "==============================================================================\n"
                  << "Main Menu Options:\n"
                  << "  [1] Digital Data Stream Generator (Random, 4/8-Zero Injected, Custom)\n"
                  << "  [2] Competitive String Coding: Manacher's O(N) Palindromic Search\n"
                  << "  [3] Baseband Line Coding (NRZ-L, NRZ-I, Manchester, Diff Manchester, AMI)\n"
                  << "  [4] Scrambling State Machines: B8ZS & HDB3 with Violation Inspection\n"
                  << "  [5] Analog Modulation: Continuous Wave, Nyquist Sampling & Uniform PCM\n"
                  << "  [6] Delta Modulation (DM): 1-Bit Tracking, Slope Overload & Noise\n"
                  << "  [7] Full End-to-End Integrated Transmission Pipeline\n"
                  << "  [8] System Help & Architectural Documentation\n"
                  << "  [0] Exit\n"
                  << "Active Bitstream (" << current_bitstream_.size() << " bits): " << current_bitstream_ << "\n"
                  << "Enter selection [0-8]: ";

        int choice = -1;
        if (!(std::cin >> choice)) {
            std::cin.clear();
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            break;
        }

        if (choice == 0) {
            std::cout << "Exiting. Thank you!\n";
            break;
        } else if (choice == 1) {
            menu_generator();
        } else if (choice == 2) {
            menu_palindrome();
        } else if (choice == 3) {
            menu_line_coding();
        } else if (choice == 4) {
            menu_scrambling();
        } else if (choice == 5) {
            menu_analog_pcm();
        } else if (choice == 6) {
            menu_delta_modulation();
        } else if (choice == 7) {
            menu_pipeline();
        } else if (choice == 8) {
            show_help_guide();
        } else {
            std::cout << "Invalid choice. Please select an option between 0 and 8.\n";
        }
    }
}

} // namespace cli
} // namespace dc
