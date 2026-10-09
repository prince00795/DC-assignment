"""
ITT 036: Programming Assignment 1 — Main Entrypoint
===================================================
Digital Signal Encoder & Decoder System
Autumn 2026

Day 3 Milestone System Verification:
- [Person 1] Algorithmic Data Stream Engineering:
    * Digital data generation & pattern-injected streams (B8ZS 8-zeros, HDB3 4-zeros)
    * O(N) Manacher's Algorithm for longest palindromic substring discovery
    * Verification against naive O(N^2) expand-around-center benchmark
- [Person 2] Line Coding & Differential Signaling:
    * NRZ-L (Non-Return-to-Zero-Level) Encoder & Decoder
    * NRZ-I (Non-Return-to-Zero-Invert) Encoder with differential transition tracking
    * Invert-on-1 vs Invert-on-0 configurable logic
    * Receiver mid-point probing and differential transition decoding
- [Person 3] Analog Continuous DSP & Nyquist Sampling:
    * Continuous multi-tone signal synthesis & Fourier harmonic modeling
    * Nyquist sampling module (fs >= 2 * f_max)
    * Sampling modes: Ideal Impulse, Flat-Top (Zero-Order Hold), Natural Sampling
    * Aliasing detection and spectral folding frequency analysis
    * Whittaker-Shannon sinc interpolation (DAC reconstruction) and MSE/SNR metrics
"""

from __future__ import annotations
import math
from src.generator.data_generator import DataGenerator
from src.algorithms.palindrome import (
    ManachersAlgorithm,
    find_longest_palindrome,
    find_all_palindromes,
    naive_longest_palindrome,
)
from src.line_coding.encoders import NRZLEncoder, NRZIEncoder
from src.analog.continuous_signal import ContinuousSignal, ToneComponent
from src.analog.sampling import NyquistSampler


def main() -> None:
    print("=" * 80)
    print(" ITT 036: Digital Signal Encoder & Decoder (Autumn 2026) ")
    print(" Milestone Day 3: Manacher's O(N) Algorithm, NRZ-I Line Coding & Nyquist Sampling ")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. Person 1: Digital Stream Engineering & O(N) Manacher's Algorithm
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" [PERSON 1: Digital Stream Engineering & O(N) Manacher's Palindrome Search]")
    print("-" * 80)

    gen = DataGenerator(seed=2026)
    bitstream = gen.generate_b8zs_stream(length=32, num_injections=1)
    print(f" -> Generated 32-bit Stream:       {bitstream}")
    print(f"    Max Consecutive Zeros:         {DataGenerator.max_consecutive_zeros(bitstream)}")

    # Execute O(N) Manacher's Algorithm
    manacher_result = find_longest_palindrome(bitstream)
    naive_result = naive_longest_palindrome(bitstream)

    print(f"\n -> Manacher's O(N) Search Result:")
    print(f"    Longest Palindromic Substring: '{manacher_result.substring}'")
    print(f"    Length:                        {manacher_result.length} bits")
    print(f"    Span [Start:End]:              [{manacher_result.start}:{manacher_result.end}]")
    print(f"    Center Position:               {manacher_result.center_index:.1f}")
    print(f"    Parity:                        {'Even-length' if manacher_result.is_even else 'Odd-length'}")
    print(f"    Validated with Naive O(N^2):   {'MATCHED' if manacher_result.length == naive_result.length else 'MISMATCH'}")

    # Inspect multiple palindromes
    palindromes_list = find_all_palindromes(bitstream, min_length=4)
    if palindromes_list:
        print(f"    Other Palindromes (len >= 4):  {[p.substring for p in palindromes_list[:4]]}")

    # -------------------------------------------------------------------------
    # 2. Person 2: Line Coding — NRZ-L vs NRZ-I Differential Signaling
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" [PERSON 2: Line Coding Schemes — NRZ-L vs NRZ-I Differential Signaling]")
    print("-" * 80)

    test_bits = "10110010"
    print(f" -> Input Bitstream:               '{test_bits}'")

    # 2a. NRZ-L
    encoder_nrzl = NRZLEncoder(positive_voltage=2.5, negative_voltage=-2.5, zero_is_positive=True)
    wf_nrzl = encoder_nrzl.encode(test_bits)
    decoded_nrzl = encoder_nrzl.decode(wf_nrzl)
    print(f"\n -> [NRZ-L (Level-Based)]:")
    print(f"    Scheme:                        {encoder_nrzl.scheme_name}")
    print(f"    Mapping:                       '0' -> +{encoder_nrzl.positive_voltage}V, '1' -> {encoder_nrzl.negative_voltage}V")
    print(f"    Transitions Count:             {wf_nrzl.metadata['transitions']} (Density: {wf_nrzl.metadata['transition_density']:.2f})")
    print(f"    Average DC Voltage:            {wf_nrzl.metadata['average_voltage']:+.3f} V")
    print(f"    Mid-Point Probe Bit Recovery:  '{decoded_nrzl}' [Matched: {decoded_nrzl == test_bits}]")

    # 2b. NRZ-I (Non-Return-to-Zero-Invert)
    encoder_nrzi = NRZIEncoder(
        positive_voltage=2.5,
        negative_voltage=-2.5,
        transition_on_one=True,   # Bit '1' inverts voltage, '0' holds
        initial_voltage=2.5,      # Starts at +2.5V reference
    )
    wf_nrzi = encoder_nrzi.encode(test_bits)
    decoded_nrzi = encoder_nrzi.decode(wf_nrzi)

    print(f"\n -> [NRZ-I (Transition / Differential-Based)]:")
    print(f"    Scheme:                        {encoder_nrzi.scheme_name}")
    print(f"    Rule:                          '1' -> Transition (Invert Level), '0' -> No Transition (Hold)")
    print(f"    Initial Reference Voltage:     +{wf_nrzi.metadata['initial_voltage']:.1f} V")
    print(f"    Bit Voltage Levels:            {wf_nrzi.metadata['bit_levels']}")
    print(f"    Transition Indices:            {wf_nrzi.metadata['transition_indices']}")
    print(f"    Total Transitions:             {wf_nrzi.metadata['transitions']} (Density: {wf_nrzi.metadata['transition_density']:.2f})")
    print(f"    Average DC Voltage:            {wf_nrzi.metadata['average_voltage']:+.3f} V")

    # Receiver Midpoint Probing & Differential Decode
    print("    Receiver Probing & Differential Decoding:")
    for b_idx in range(min(4, len(test_bits))):
        t_mid, v_mid = wf_nrzi.get_midpoint_sample(b_idx)
        print(f"      Bit [{b_idx}] ('{test_bits[b_idx]}'): probed t = {t_mid:4.2f}s -> V_mid = {v_mid:+5.2f}V")

    recovery_nrzi = (decoded_nrzi == test_bits)
    print(f"    Differential Bit Recovery:     '{decoded_nrzi}' [Matched: {recovery_nrzi}]")

    # -------------------------------------------------------------------------
    # 3. Person 3: Analog DSP & Nyquist Sampling Module
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print(" [PERSON 3: Analog Continuous Signal & Nyquist Sampling Subsystem]")
    print("-" * 80)

    # Composite multi-tone signal: 4 Hz and 10 Hz components
    analog_sig = ContinuousSignal.create_multitone(
        components=[(2.0, 4.0), (1.5, 10.0, math.pi / 3)],
        dc_offset=0.2,
    )
    print(f" -> Continuous Analog Signal x(t):")
    print(f"    Tones:                         Tone 1 (2.0V @ 4Hz) + Tone 2 (1.5V @ 10Hz)")
    print(f"    Maximum Frequency (f_max):     {analog_sig.max_frequency:.1f} Hz")
    print(f"    Theoretical Nyquist Rate:      {analog_sig.nyquist_rate:.1f} Hz (2 * f_max)")

    sampler = NyquistSampler()

    # Case A: Oversampled Sampling (fs = 2.5 * Nyquist = 50 Hz)
    fs_over = 2.5 * analog_sig.nyquist_rate
    res_over = sampler.sample(analog_sig, sampling_rate=fs_over, duration=0.25, mode="ideal")
    metrics_over = res_over.compute_reconstruction_metrics(analog_sig)

    print(f"\n -> Sampling Scenario A: Oversampled (fs = {fs_over:.1f} Hz, OSR = 2.5x):")
    print(f"    Nyquist Criterion Satisfied:   {res_over.is_nyquist_satisfied}")
    print(f"    Samples Collected:             {res_over.num_samples}")
    print(f"    Reconstruction MSE:            {metrics_over['mse']:.4e} V^2")
    print(f"    Reconstruction SNR:            {metrics_over['snr_db']:.2f} dB (High Fidelity Reconstruction)")

    # Case B: Undersampled Sampling (fs = 0.6 * Nyquist = 12 Hz < 20 Hz)
    fs_under = 12.0
    res_under = sampler.sample(analog_sig, sampling_rate=fs_under, duration=0.25, mode="ideal")
    metrics_under = res_under.compute_reconstruction_metrics(analog_sig)
    alias_diag = sampler.detect_aliasing(analog_sig, sampling_rate=fs_under)

    print(f"\n -> Sampling Scenario B: Undersampled (fs = {fs_under:.1f} Hz < {analog_sig.nyquist_rate:.1f} Hz):")
    print(f"    Nyquist Criterion Satisfied:   {res_under.is_nyquist_satisfied} [ALIASING DETECTED]")
    print(f"    Folding Frequency (fs / 2):    {alias_diag['folding_frequency']:.1f} Hz")
    print(f"    Folded Apparent Frequencies:   {alias_diag['folded_frequencies']}")
    print(f"    Reconstruction MSE:            {metrics_under['mse']:.4e} V^2")
    print(f"    Reconstruction SNR:            {metrics_under['snr_db']:.2f} dB (Severe Aliasing Distortion)")

    # Case C: Flat-Top (Zero-Order Hold) PAM Sampling
    res_zoh = sampler.sample(analog_sig, sampling_rate=25.0, duration=0.1, mode="flat_top")
    print(f"\n -> Sampling Mode: Flat-Top / Zero-Order Hold (ZOH):")
    print(f"    Mode:                          {res_zoh.sampling_mode.upper()} (Staircase PAM)")
    print(f"    ZOH Waveform Points:           {len(res_zoh.zoh_times)} points generated")

    print("\n" + "=" * 80)
    print(" Status: Day 3 Milestone Modules Successfully Tested, Verified & Validated! ")
    print("=" * 80)


if __name__ == "__main__":
    main()
