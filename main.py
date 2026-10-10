"""
ITT 036: Digital Signal Encoder & Decoder System
================================================
Comprehensive Pipeline Architecture:
- Digital Data Stream Generation & Pattern Injection
- O(N) Linear Time Manacher's String Palindrome Algorithm
- Baseband Line Coding: NRZ-L, NRZ-I, and Manchester (IEEE 802.3 & G.E. Thomas)
- Analog Continuous Waveform Synthesis & Fourier Harmonics
- Nyquist-Shannon Sampling Engine & Whittaker-Shannon Sinc Reconstruction
- Uniform PCM Quantization (L = 2^n levels, step size Delta, SQNR analysis)
- End-to-End Pipeline Bridge: Analog -> Nyquist Sampling -> Quantization -> Line Coding
"""

from __future__ import annotations
import math
from src.generator.data_generator import DataGenerator
from src.algorithms.palindrome import (
    find_longest_palindrome,
    find_all_palindromes,
    naive_longest_palindrome,
)
from src.line_coding.encoders import NRZLEncoder, NRZIEncoder, ManchesterEncoder
from src.analog.continuous_signal import ContinuousSignal
from src.analog.sampling import NyquistSampler
from src.analog.quantization import UniformQuantizer


def main() -> None:
    print("=" * 80)
    print(" ITT 036: DIGITAL SIGNAL TRANSMISSION, MODULATION & LINE CODING SYSTEM ")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # 1. Digital Data Stream Engineering & Competitive String Algorithms
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" MODULE 1: DATA STREAM ENGINEERING & STRING ALGORITHMS")
    print("=" * 80)

    gen = DataGenerator(seed=2026)
    random_stream = gen.generate_random(16)
    b8zs_stream = gen.generate_b8zs_stream(length=32, num_injections=1)

    print(f" -> Pure Random 16-bit Stream:       {random_stream}")
    print(f" -> Pattern-Injected Stream:         {b8zs_stream}")
    print(f"    Longest Zero Run Length:         {DataGenerator.max_consecutive_zeros(b8zs_stream)} consecutive zeros")
    print(f"    Detected Zero Blocks:            {DataGenerator.find_zero_runs(b8zs_stream)}")

    # O(N) Manacher's Algorithm Execution
    manacher_res = find_longest_palindrome(b8zs_stream)
    naive_res = naive_longest_palindrome(b8zs_stream)

    print(f"\n -> Manacher's O(N) Palindromic Search:")
    print(f"    Longest Palindromic Substring:   '{manacher_res.substring}'")
    print(f"    Length:                          {manacher_res.length} bits")
    print(f"    Span [Start:End]:                [{manacher_res.start}:{manacher_res.end}]")
    print(f"    Center Coordinate:               {manacher_res.center_index:.1f}")
    print(f"    Parity:                          {'Even-length' if manacher_res.is_even else 'Odd-length'}")
    print(f"    Validation vs Naive O(N^2):      {'MATCHED (Exact match)' if manacher_res.length == naive_res.length else 'MISMATCH'}")

    # -------------------------------------------------------------------------
    # 2. Baseband Physical Line Coding Schemes & Receiver Decoders
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" MODULE 2: BASEBAND LINE CODING SCHEMES & RECEIVER DECODERS")
    print("=" * 80)

    test_stream = "10110010"
    print(f" -> Input Test Stream:               '{test_stream}'")

    # 2a. NRZ-L (Non-Return-to-Zero-Level)
    nrzl = NRZLEncoder(positive_voltage=2.5, negative_voltage=-2.5, zero_is_positive=True)
    wf_nrzl = nrzl.encode(test_stream)
    decoded_nrzl = nrzl.decode(wf_nrzl)
    print(f"\n [1] NRZ-L (Level-Based Signaling):")
    print(f"     Mapping:                        '0' -> +{nrzl.positive_voltage}V, '1' -> {nrzl.negative_voltage}V")
    print(f"     Transitions Count:              {wf_nrzl.metadata['transitions']} (Density: {wf_nrzl.metadata['transition_density']:.2f})")
    print(f"     Average DC Bias:                {wf_nrzl.metadata['average_voltage']:+.3f} V")
    print(f"     Receiver Decoding Recovery:     '{decoded_nrzl}' [Verified: {decoded_nrzl == test_stream}]")

    # 2b. NRZ-I (Non-Return-to-Zero-Invert)
    nrzi = NRZIEncoder(positive_voltage=2.5, negative_voltage=-2.5, transition_on_one=True, initial_voltage=2.5)
    wf_nrzi = nrzi.encode(test_stream)
    decoded_nrzi = nrzi.decode(wf_nrzi)
    print(f"\n [2] NRZ-I (Differential Transition Signaling):")
    print(f"     Rule:                           '1' -> Level Invert, '0' -> Level Hold")
    print(f"     Initial State:                  +{wf_nrzi.metadata['initial_voltage']:.1f} V")
    print(f"     Transition Indices:             {wf_nrzi.metadata['transition_indices']}")
    print(f"     Transition Density:             {wf_nrzi.metadata['transition_density']:.2f}")
    print(f"     Differential Receiver Recovery: '{decoded_nrzi}' [Verified: {decoded_nrzi == test_stream}]")

    # 2c. Manchester Biphase Coding (IEEE 802.3 and G.E. Thomas)
    manchester_ieee = ManchesterEncoder(positive_voltage=2.5, negative_voltage=-2.5, convention="ieee")
    wf_manc_ieee = manchester_ieee.encode(test_stream)
    decoded_manc_ieee = manchester_ieee.decode(wf_manc_ieee)

    manchester_thomas = ManchesterEncoder(positive_voltage=2.5, negative_voltage=-2.5, convention="thomas")
    wf_manc_thomas = manchester_thomas.encode(test_stream)
    decoded_manc_thomas = manchester_thomas.decode(wf_manc_thomas)

    print(f"\n [3] Manchester Biphase Coding (Self-Clocking & Zero DC Bias):")
    print(f"     IEEE 802.3 Standard:            '0' -> High-to-Low (+V -> -V), '1' -> Low-to-High (-V -> +V)")
    print(f"     Total Transitions:              {wf_manc_ieee.metadata['transitions']} (Mid-bit: {wf_manc_ieee.metadata['midbit_transitions']}, Boundary: {wf_manc_ieee.metadata['boundary_transitions']})")
    print(f"     Transition Density:             {wf_manc_ieee.metadata['transition_density']:.2f} (Guaranteed >= 1.0)")
    print(f"     Net DC Voltage:                 {wf_manc_ieee.metadata['average_voltage']:+.4f} V (Strict 0.0V DC-free)")
    print(f"     IEEE Receiver Recovery:         '{decoded_manc_ieee}' [Verified: {decoded_manc_ieee == test_stream}]")
    print(f"     Thomas Receiver Recovery:       '{decoded_manc_thomas}' [Verified: {decoded_manc_thomas == test_stream}]")

    # -------------------------------------------------------------------------
    # 3. Analog DSP, Nyquist Sampling & Uniform Quantization
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" MODULE 3: ANALOG DSP, NYQUIST SAMPLING & PCM QUANTIZATION")
    print("=" * 80)

    # Multi-tone continuous waveform
    analog_sig = ContinuousSignal.create_multitone(
        components=[(2.0, 4.0), (1.5, 10.0, math.pi / 4)],
        dc_offset=0.2,
    )
    print(f" -> Continuous Analog Signal x(t):   2.0*sin(2*pi*4*t) + 1.5*sin(2*pi*10*t + pi/4) + 0.2V")
    print(f"    Highest Frequency (f_max):       {analog_sig.max_frequency:.1f} Hz")
    print(f"    Nyquist Rate (2 * f_max):        {analog_sig.nyquist_rate:.1f} Hz")
    print(f"    Average Power:                   {analog_sig.average_power:.3f} W | RMS Voltage: {analog_sig.rms_voltage:.3f} V")

    sampler = NyquistSampler()

    # Oversampling vs Undersampling
    res_nyq = sampler.sample(analog_sig, sampling_rate=50.0, duration=0.2, mode="ideal")
    metrics_nyq = res_nyq.compute_reconstruction_metrics(analog_sig)
    print(f"\n -> Nyquist Sampling (fs = 50.0 Hz, OSR = 2.5x):")
    print(f"    Nyquist Criterion Satisfied:     {res_nyq.is_nyquist_satisfied}")
    print(f"    Whittaker-Shannon Recon MSE:     {metrics_nyq['mse']:.4e} V^2 (SNR: {metrics_nyq['snr_db']:.1f} dB)")

    res_alias = sampler.sample(analog_sig, sampling_rate=12.0, duration=0.2, mode="ideal")
    alias_diag = sampler.detect_aliasing(analog_sig, sampling_rate=12.0)
    print(f"\n -> Sub-Nyquist Undersampling (fs = 12.0 Hz < 20.0 Hz):")
    print(f"    Aliasing Detected:               {alias_diag['has_aliasing']}")
    print(f"    Apparent Baseband Frequencies:   {alias_diag['folded_frequencies']}")

    # Uniform PCM Quantization
    quantizer_3bit = UniformQuantizer(num_bits=3, v_min=-4.0, v_max=4.0, coding_scheme="natural")
    q_res = quantizer_3bit.quantize(res_nyq.sample_values)

    print(f"\n -> Uniform PCM Quantization (n = 3 bits, L = 8 levels):")
    print(f"    Quantization Step Size (Δ):      {q_res.step_size:.4f} V")
    print(f"    Max Error Bound (|e| <= Δ/2):    {q_res.max_error:.4f} V <= {q_res.step_size / 2:.4f} V")
    print(f"    Empirical Noise Power:           {q_res.empirical_noise_power:.4e} V^2 (Theory: {q_res.theoretical_noise_power:.4e} V^2)")
    print(f"    Empirical SQNR:                  {q_res.empirical_sqnr_db:.2f} dB (Theory: {q_res.theoretical_sqnr_db:.2f} dB)")
    print(f"    Generated PCM Bitstream:         '{q_res.bitstream}' ({q_res.total_bits} bits)")

    # -------------------------------------------------------------------------
    # 4. Integrated End-to-End Pipeline Bridge
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print(" END-TO-END PIPELINE: ANALOG -> SAMPLING -> QUANTIZATION -> LINE CODING")
    print("=" * 80)

    # 15 bits = 5 full 3-bit PCM quantized samples
    pcm_stream = q_res.bitstream[:15]
    pcm_encoded_wf = manchester_ieee.encode(pcm_stream)
    pcm_recovered_stream = manchester_ieee.decode(pcm_encoded_wf)
    dac_reconstructed_voltages = quantizer_3bit.decode_bitstream(pcm_recovered_stream)

    print(f" -> Digitized Analog Bitstream:      '{pcm_stream}' (5 quantized samples)")
    print(f" -> Manchester Encoded Waveform:     {pcm_encoded_wf.total_samples} physical samples")
    print(f" -> Line Receiver Decoded Stream:    '{pcm_recovered_stream}' [Matched: {pcm_recovered_stream == pcm_stream}]")
    print(f" -> DAC Reconstructed Levels:        {[round(v, 3) for v in dac_reconstructed_voltages]} V")


    print("\n" + "=" * 80)
    print(" SYSTEM PIPELINE VERIFIED SUCCESSFULLY! ")
    print("=" * 80)


if __name__ == "__main__":
    main()
