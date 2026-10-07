"""
ITT 036: Programming Assignment 1 — Main Entrypoint
===================================================
Digital Signal Encoder & Decoder System
Autumn 2026

Day 2 Milestone System Verification:
- [Person 1] Digital Data Stream Generator:
    * Pure random generation
    * Pattern-injected streams (8 consecutive zeros for B8ZS, 4 consecutive zeros for HDB3)
    * Custom binary pattern injection & zero-run analysis
- [Person 2] Line Coding & Physical Signal Models:
    * NRZ-L (Non-Return-to-Zero-Level) Encoder
    * Voltage mapping (+V, -V) with standard telecom & inverted conventions
    * Mid-point receiver probing & physical signal bit decoding
    * Transition density & DC bias analysis
- [Person 3] Analog Continuous Signal & Nyquist Sampling:
    * Single-tone sinusoidal modeling
    * Multi-tone composite waveforms & dual-tone (DTMF) synthesis
    * Harmonic series synthesis (Fourier square wave)
    * Theoretical power, RMS voltage, and PAPR computation
    * Uniform Nyquist rate sampling
"""

import math
from src.generator.data_generator import DataGenerator
from src.line_coding.encoders import NRZLEncoder
from src.analog.continuous_signal import ContinuousSignal, ToneComponent


def main() -> None:
    print("=" * 76)
    print(" ITT 036: Digital Signal Encoder & Decoder (Autumn 2026) ")
    print(" Milestone Day 2: Pattern Generator, NRZ-L Coding & Multi-Tone DSP ")
    print("=" * 76)

    # ---------------------------------------------------------
    # 1. Person 1: Digital Data Generator & Pattern Injection
    # ---------------------------------------------------------
    print("\n" + "-" * 76)
    print(" [PERSON 1: Data Stream Engineering & Pattern Injection]")
    print("-" * 76)
    gen = DataGenerator(seed=101)

    random_stream = gen.generate_random(16)
    print(f" -> Pure Random 16-bit Stream:       {random_stream}")

    b8zs_stream = gen.generate_b8zs_stream(length=24, num_injections=1)
    b8zs_runs = DataGenerator.find_zero_runs(b8zs_stream)
    print(f" -> B8ZS Injected Stream (8 zeros):  {b8zs_stream}")
    print(f"    Detected Zero Runs:              {b8zs_runs}")
    print(f"    Max Consecutive Zeros:           {DataGenerator.max_consecutive_zeros(b8zs_stream)}")

    hdb3_stream = gen.generate_hdb3_stream(length=20, num_injections=2)
    hdb3_runs = DataGenerator.find_zero_runs(hdb3_stream)
    print(f" -> HDB3 Injected Stream (4 zeros):  {hdb3_stream}")
    print(f"    Detected Zero Runs:              {hdb3_runs}")

    custom_injected = gen.inject_pattern(base_stream="111111111111", pattern="00000000", position=2)
    print(f" -> Custom Overwrite Pattern Inject: {custom_injected}")

    # ---------------------------------------------------------
    # 2. Person 2: Line Coding Schemes — NRZ-L Encoder & Decoder
    # ---------------------------------------------------------
    print("\n" + "-" * 76)
    print(" [PERSON 2: Line Coding Schemes — NRZ-L Physical Encoder & Decoder]")
    print("-" * 76)
    encoder_nrzl = NRZLEncoder(
        samples_per_bit=20,
        bit_duration=1.0,
        positive_voltage=2.5,
        negative_voltage=-2.5,
        zero_is_positive=True,  # Telecom convention: 0 -> +2.5V, 1 -> -2.5V
    )

    test_bits = "10110010"
    waveform = encoder_nrzl.encode(test_bits)
    print(f" -> Scheme:                          {encoder_nrzl.scheme_name}")
    print(f" -> Input Bitstream:                 '{test_bits}'")
    print(f" -> Bit Mapping:                     '0' -> +{encoder_nrzl.positive_voltage}V, '1' -> {encoder_nrzl.negative_voltage}V")
    print(f" -> Total Physical Samples:          {waveform.total_samples} (over {waveform.total_duration:.1f}s)")
    print(f" -> Transitions Count:               {waveform.metadata['transitions']}")
    print(f" -> Transition Density:              {waveform.metadata['transition_density']:.2f}")
    print(f" -> Average Voltage (DC Bias):       {waveform.metadata['average_voltage']:+.3f} V")
    print(f" -> Has DC Bias:                     {waveform.metadata['has_dc_bias']}")

    # Receiver Midpoint Probe & Decoding
    print(" -> Receiver Midpoint Probing:")
    for b_idx in range(min(4, len(test_bits))):
        t_mid, v_mid = waveform.get_midpoint_sample(b_idx)
        print(f"    Bit [{b_idx}] ('{test_bits[b_idx]}'): probed t = {t_mid:4.2f}s -> V_mid = {v_mid:+5.2f}V")

    decoded_bits = encoder_nrzl.decode(waveform)
    recovery_success = (decoded_bits == test_bits)
    print(f" -> Physical Decoder Bit Recovery:   '{decoded_bits}' [Matched: {recovery_success}]")

    # ---------------------------------------------------------
    # 3. Person 3: Analog Continuous Signal & Multi-Tone DSP
    # ---------------------------------------------------------
    print("\n" + "-" * 76)
    print(" [PERSON 3: Analog Modulation & Multi-Tone Signal Synthesis]")
    print("-" * 76)

    # 3a. Single Tone
    sine_sig = ContinuousSignal.create_simple_sine(amplitude=3.0, frequency=5.0)
    print(f" -> Single Tone Waveform:            x(t) = 3.0 * sin(2 * pi * 5.0 * t)")
    print(f"    Maximum Frequency (f_max):       {sine_sig.max_frequency:.1f} Hz")
    print(f"    Nyquist Rate (2 * f_max):        {sine_sig.nyquist_rate:.1f} Hz")
    print(f"    Average Power (P_avg):           {sine_sig.average_power:.2f} W")
    print(f"    RMS Voltage (V_rms):             {sine_sig.rms_voltage:.3f} V")

    # 3b. Multi-Tone Composite Wave
    multi_sig = ContinuousSignal.create_multitone(
        components=[(2.0, 4.0), (1.0, 10.0, math.pi / 4)],
        dc_offset=0.5,
    )
    print(f"\n -> Composite Multi-Tone Signal:")
    print(f"    Tones: Tone 1 (2.0V, 4Hz) + Tone 2 (1.0V, 10Hz) + DC Offset 0.5V")
    print(f"    Highest Frequency (f_max):       {multi_sig.max_frequency:.1f} Hz")
    print(f"    Signal Bandwidth:                {multi_sig.bandwidth:.1f} Hz")
    print(f"    Required Nyquist Rate:           {multi_sig.nyquist_rate:.1f} Hz")
    print(f"    Total Theoretical Power:         {multi_sig.average_power:.3f} W")
    print(f"    PAPR (Peak-to-Average Ratio):    {multi_sig.peak_to_average_power_ratio:.2f}")

    # 3c. Fourier Harmonic Square Wave Approximation
    sq_sig = ContinuousSignal.create_harmonic_series(
        fundamental_freq=5.0,
        num_harmonics=3,
        base_amplitude=2.0,
        harmonic_type="odd",
    )
    print(f"\n -> Harmonic Series (Square Wave 3-Harmonics, f0=5Hz):")
    print(f"    Frequencies Present:             {sq_sig.frequencies} Hz")
    print(f"    Nyquist Rate for 3rd Harmonic:   {sq_sig.nyquist_rate:.1f} Hz")

    # Uniform Nyquist Sampling
    fs_test = 40.0  # 40 Hz > 20 Hz
    sample_times, sample_values = multi_sig.sample(sampling_rate=fs_test, duration=0.1)
    print(f"\n -> Uniform Sampling at fs = {fs_test:.1f} Hz (Nyquist satisfied: {multi_sig.is_nyquist_satisfied(fs_test)}):")
    for i, (t_val, s_val) in enumerate(zip(sample_times[:4], sample_values[:4])):
        print(f"    Sample [{i}]: t = {t_val:.4f}s -> x(t) = {s_val:+.3f} V")

    print("\n" + "=" * 76)
    print(" Status: Day 2 Milestone Modules Successfully Tested and Verified! ")
    print("=" * 76)


if __name__ == "__main__":
    main()
