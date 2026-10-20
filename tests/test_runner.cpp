#include "algorithms/palindrome.hpp"
#include "generator/data_generator.hpp"
#include "line_coding/encoders.hpp"
#include "scrambling/b8zs.hpp"
#include "scrambling/hdb3.hpp"
#include "decoder/signal_decoder.hpp"
#include "analog/continuous_signal.hpp"
#include "analog/sampling.hpp"
#include "analog/quantization.hpp"
#include "analog/delta_modulation.hpp"
#include "pipeline/bridge.hpp"
#include <iostream>
#include <cassert>
#include <cmath>
#include <chrono>

using namespace dc;

static int g_tests_run = 0;
static int g_tests_passed = 0;

#define TEST_ASSERT(cond, msg) \
    do { \
        g_tests_run++; \
        if (!(cond)) { \
            std::cerr << "[-] FAILED: " << msg << " (" << __FILE__ << ":" << __LINE__ << ")\n"; \
        } else { \
            g_tests_passed++; \
        } \
    } while (0)

void test_generator() {
    generator::DataGenerator gen(42);

    // Random generation
    std::string s = gen.generate_random(50);
    TEST_ASSERT(s.size() == 50, "Random stream size 50");
    TEST_ASSERT(generator::DataGenerator::validate_stream(s), "Random stream binary validation");

    // Zero runs
    std::string b8zs_stream = gen.generate_b8zs_stream(40, 2);
    TEST_ASSERT(b8zs_stream.size() == 40, "B8ZS stream size 40");
    TEST_ASSERT(generator::DataGenerator::max_consecutive_zeros(b8zs_stream) >= 8, "B8ZS zero run >= 8");

    std::string hdb3_stream = gen.generate_hdb3_stream(30, 2);
    TEST_ASSERT(hdb3_stream.size() == 30, "HDB3 stream size 30");
    TEST_ASSERT(generator::DataGenerator::max_consecutive_zeros(hdb3_stream) >= 4, "HDB3 zero run >= 4");

    // Pattern injection
    std::string base = "11111111";
    std::string injected = gen.inject_pattern(base, "0000", 2, true);
    TEST_ASSERT(injected == "11000011", "Pattern injection overwrite");

    std::string inserted = gen.inject_pattern("1111", "00", 2, false);
    TEST_ASSERT(inserted == "110011", "Pattern injection insert");
}

void test_palindrome() {
    // Basic checks
    TEST_ASSERT(algorithms::is_palindrome("racecar"), "racecar is palindrome");
    TEST_ASSERT(algorithms::is_palindrome("1001"), "1001 is palindrome");
    TEST_ASSERT(!algorithms::is_palindrome("1010"), "1010 is not palindrome");

    // Manacher odd & even
    algorithms::ManachersAlgorithm m1("babad");
    auto res1 = m1.find_longest();
    TEST_ASSERT(res1.length == 3 && (res1.substring == "bab" || res1.substring == "aba"), "babad longest palindrome");

    algorithms::ManachersAlgorithm m2("cbbd");
    auto res2 = m2.find_longest();
    TEST_ASSERT(res2.length == 2 && res2.substring == "bb" && res2.is_even, "cbbd even palindrome");

    // Fuzz against naive algorithm
    generator::DataGenerator gen(999);
    for (int len : {10, 25, 50, 100}) {
        for (int i = 0; i < 5; ++i) {
            std::string stream = gen.generate_random(len);
            auto man_res = algorithms::find_longest_palindrome(stream);
            auto naive_res = algorithms::naive_longest_palindrome(stream);
            TEST_ASSERT(man_res.length == naive_res.length, "Manacher vs Naive length match");
            TEST_ASSERT(algorithms::is_palindrome(man_res.substring), "Manacher substring is valid palindrome");
        }
    }
}

void test_line_coding() {
    std::string test_stream = "1011001";
    decoder::PhysicalSignalDecoder decoder;

    // NRZ-L
    line_coding::NRZLEncoder nrz_l(true, 50, 1.0, 1.0, -1.0);
    auto wf_l = nrz_l.encode(test_stream);
    TEST_ASSERT(nrz_l.decode(wf_l) == test_stream, "NRZ-L internal decode");
    TEST_ASSERT(decoder.decode(wf_l).recovered_bits == test_stream, "NRZ-L physical decode");

    // NRZ-I
    line_coding::NRZIEncoder nrz_i(std::nullopt, 50, 1.0, 1.0, -1.0);
    auto wf_i = nrz_i.encode(test_stream);
    TEST_ASSERT(nrz_i.decode(wf_i) == test_stream, "NRZ-I internal decode");
    TEST_ASSERT(decoder.decode(wf_i).recovered_bits == test_stream, "NRZ-I physical decode");

    // Manchester IEEE & Thomas
    line_coding::ManchesterEncoder man_ieee(line_coding::ManchesterConvention::IEEE, 50);
    auto wf_m_ieee = man_ieee.encode(test_stream);
    TEST_ASSERT(man_ieee.decode(wf_m_ieee) == test_stream, "Manchester IEEE internal decode");
    TEST_ASSERT(decoder.decode(wf_m_ieee).recovered_bits == test_stream, "Manchester IEEE physical decode");

    line_coding::ManchesterEncoder man_thomas(line_coding::ManchesterConvention::Thomas, 50);
    auto wf_m_thomas = man_thomas.encode(test_stream);
    TEST_ASSERT(man_thomas.decode(wf_m_thomas) == test_stream, "Manchester Thomas internal decode");
    TEST_ASSERT(decoder.decode(wf_m_thomas).recovered_bits == test_stream, "Manchester Thomas physical decode");

    // Differential Manchester
    line_coding::DifferentialManchesterEncoder diff_man(-1.0, 50);
    auto wf_dm = diff_man.encode(test_stream);
    TEST_ASSERT(diff_man.decode(wf_dm) == test_stream, "Diff Manchester internal decode");
    TEST_ASSERT(decoder.decode(wf_dm).recovered_bits == test_stream, "Diff Manchester physical decode");

    // AMI
    line_coding::AMIEncoder ami(std::nullopt, 50);
    auto wf_ami = ami.encode(test_stream);
    TEST_ASSERT(ami.decode(wf_ami) == test_stream, "AMI internal decode");
    TEST_ASSERT(decoder.decode(wf_ami).recovered_bits == test_stream, "AMI physical decode");
}

void test_scrambling() {
    decoder::PhysicalSignalDecoder decoder;

    // B8ZS: previous pulse positive (+2.0)
    scrambling::B8ZSScrambler b8zs(2.0, -2.0, 0.0);
    std::string stream8 = "100000000"; // '1' becomes +2.0 if initial_polarity = -2.0
    auto [pulses_pos, subs_pos] = b8zs.scramble(stream8, -2.0);
    TEST_ASSERT(subs_pos.size() == 1, "B8ZS substitution count");
    TEST_ASSERT(subs_pos[0].rule_applied == "000+-0-+", "B8ZS positive rule");
    TEST_ASSERT(b8zs.descramble(pulses_pos) == stream8, "B8ZS descramble recovery positive");

    // B8ZS: previous pulse negative (-2.0)
    auto [pulses_neg, subs_neg] = b8zs.scramble(stream8, 2.0);
    TEST_ASSERT(subs_neg.size() == 1, "B8ZS substitution count");
    TEST_ASSERT(subs_neg[0].rule_applied == "000-+0+-", "B8ZS negative rule");
    TEST_ASSERT(b8zs.descramble(pulses_neg) == stream8, "B8ZS descramble recovery negative");

    // B8ZS Waveform encode & decode
    auto wf_b8zs = b8zs.encode("100000000100000000");
    TEST_ASSERT(b8zs.decode(wf_b8zs) == "100000000100000000", "B8ZS double block decode");
    TEST_ASSERT(decoder.decode(wf_b8zs).recovered_bits == "100000000100000000", "B8ZS physical decode");

    // HDB3: odd parity (000V) and even parity (B00V)
    scrambling::HDB3Scrambler hdb3(2.0, -2.0, 0.0);
    std::string stream_odd = "10000"; // 1 pulse since last -> odd parity
    auto [p_odd, s_odd] = hdb3.scramble(stream_odd);
    TEST_ASSERT(s_odd.size() == 1 && s_odd[0].rule_applied == "000V", "HDB3 000V odd parity");
    TEST_ASSERT(hdb3.descramble(p_odd) == stream_odd, "HDB3 odd parity descramble");

    std::string stream_even = "100000000"; // 2nd block has 0 pulses since last -> even parity
    auto [p_even, s_even] = hdb3.scramble(stream_even);
    TEST_ASSERT(s_even.size() == 2, "HDB3 two substitutions");
    TEST_ASSERT(s_even[1].rule_applied == "B00V", "HDB3 B00V even parity");
    TEST_ASSERT(hdb3.descramble(p_even) == stream_even, "HDB3 even parity descramble");
}

void test_analog_dsp() {
    // Continuous Signal
    auto sig = analog::ContinuousSignal::create_simple_sine(2.0, 5.0);
    TEST_ASSERT(sig.max_frequency() == 5.0, "ContinuousSignal max frequency");
    TEST_ASSERT(sig.nyquist_rate() == 10.0, "ContinuousSignal Nyquist rate = 2*f_max");
    TEST_ASSERT(std::abs(sig.rms_voltage(1.0) - (2.0 / std::sqrt(2.0))) < 0.05, "Sine RMS voltage");

    // Nyquist Sampling & Sinc Reconstruction
    analog::NyquistSampler sampler;
    auto s_res = sampler.sample(sig, 25.0, 1.0); // 2.5x Nyquist
    TEST_ASSERT(s_res.is_nyquist_satisfied, "Nyquist satisfied at 25 Hz");
    auto [mse, snr] = s_res.compute_reconstruction_metrics(sig, 1.0);
    TEST_ASSERT(snr > 30.0, "Oversampled sinc reconstruction high SNR");

    // Uniform PCM Quantizer
    analog::UniformQuantizer pcm(3, -2.0, 2.0, "natural");
    TEST_ASSERT(pcm.num_levels() == 8, "3-bit PCM 8 levels");
    TEST_ASSERT(std::abs(pcm.step_size() - 0.5) < 1e-6, "3-bit PCM step size 0.5V");
    auto q_res = pcm.quantize_samples(s_res.sample_values);
    auto rec_samples = pcm.decode_bitstream(q_res.bitstream);
    TEST_ASSERT(rec_samples.size() == s_res.sample_values.size(), "PCM decoded sample count match");

    // Delta Modulation
    analog::DeltaModulator dm(0.20, 50.0, 0.0);
    auto dm_res = dm.encode_samples(s_res.sample_values);
    auto dm_rec = dm.decode_bitstream(dm_res.bitstream);
    TEST_ASSERT(dm_rec.size() == s_res.sample_values.size(), "DM decoded count match");
}

void test_pipeline_bridge() {
    pipeline::PipelineBridge bridge(50, 1.0, 1.0, -1.0, 0.0);
    auto sig = analog::ContinuousSignal::create_simple_sine(1.5, 2.0);

    // PCM Pipeline
    auto res_pcm = bridge.run_analog_to_line_coding(sig, 20.0, 1.0, "PCM", 3, 0.25, "AMI", "B8ZS");
    TEST_ASSERT(res_pcm.verification_passed, "End-to-End PCM B8ZS Pipeline 100% recovery");
    TEST_ASSERT(res_pcm.ber == 0.0, "PCM B8ZS BER is zero");

    // DM Pipeline
    auto res_dm = bridge.run_analog_to_line_coding(sig, 25.0, 1.0, "DM", 3, 0.20, "Manchester", "None");
    TEST_ASSERT(res_dm.verification_passed, "End-to-End DM Manchester Pipeline 100% recovery");
    TEST_ASSERT(res_dm.ber == 0.0, "DM Manchester BER is zero");
}

void test_stress_validation() {
    generator::DataGenerator gen(777);
    std::string big_stream = gen.generate_b8zs_stream(50000, 500); // 50,000 bits!

    // Line coding roundtrip
    line_coding::NRZLEncoder nrz_l(true, 2);
    auto wf = nrz_l.encode(big_stream);
    std::string rec = nrz_l.decode(wf);
    TEST_ASSERT(rec == big_stream, "50,000-bit NRZ-L stress roundtrip");

    // B8ZS Scrambler stress
    scrambling::B8ZSScrambler b8zs;
    auto [pulses, subs] = b8zs.scramble(big_stream);
    std::string rec_b8zs = b8zs.descramble(pulses);
    TEST_ASSERT(rec_b8zs == big_stream, "50,000-bit B8ZS stress descramble");

    // Manacher O(N) linear time check
    auto t0 = std::chrono::high_resolution_clock::now();
    algorithms::ManachersAlgorithm m(big_stream);
    auto res = m.find_longest();
    auto t1 = std::chrono::high_resolution_clock::now();
    double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    TEST_ASSERT(ms < 500.0, "50,000-bit Manacher execution time < 500 ms (linear)");
}

int main() {
    std::cout << "\n======================================================\n";
    std::cout << " RUNNING C++20 DIGITAL COMMUNICATIONS TEST SUITE\n";
    std::cout << "======================================================\n";

    test_generator();
    test_palindrome();
    test_line_coding();
    test_scrambling();
    test_analog_dsp();
    test_pipeline_bridge();
    test_stress_validation();

    std::cout << "\n------------------------------------------------------\n";
    std::cout << " Test Results: " << g_tests_passed << " / " << g_tests_run << " passed ("
              << (g_tests_passed == g_tests_run ? "100% SUCCESS" : "SOME FAILED") << ")\n";
    std::cout << "======================================================\n\n";

    return (g_tests_passed == g_tests_run) ? 0 : 1;
}
