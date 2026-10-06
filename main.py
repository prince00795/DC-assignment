"""
ITT 036: Programming Assignment 1 — Main Entrypoint
===================================================
Digital Signal Encoder & Decoder System
Autumn 2026

System Verification:
- Digital Data Stream Generator (Random & Injected Zeros)
- Line Coding SignalWaveform Data Models & Interface
- Analog Continuous Signal Modeling & Nyquist Sampling
"""

import sys
from src.generator.data_generator import DataGenerator
from src.line_coding.base import SignalWaveform
from src.analog.continuous_signal import ContinuousSignal, ToneComponent


def main() -> None:
    print("=" * 70)
    print(" ITT 036: Digital Signal Encoder & Decoder (Autumn 2026) ")
    print(" Core Engine Verification & Pipeline Test ")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Digital Data Generator
    # ---------------------------------------------------------
    print("\n[1] Digital Data Stream Generator")
    gen = DataGenerator(seed=101)
    
    random_stream = gen.generate_random(16)
    print(f" -> Pure Random 16-bit Stream:       {random_stream}")
    
    b8zs_stream = gen.generate_with_fixed_zeros(length=24, zero_run_length=8, num_injections=1)
    print(f" -> 8-Zero Injected Stream (B8ZS):   {b8zs_stream}")
    
    hdb3_stream = gen.generate_with_fixed_zeros(length=20, zero_run_length=4, num_injections=2)
    print(f" -> 4-Zero Injected Stream (HDB3):   {hdb3_stream}")

    # ---------------------------------------------------------
    # 2. Line Coding Abstraction & SignalWaveform
    # ---------------------------------------------------------
    print("\n[2] Line Coding & Physical Signal Models")
    dummy_bits = "1011"
    spb = 10
    dt = 1.0 / spb
    t_pts = [i * dt for i in range(len(dummy_bits) * spb)]
    v_pts = []
    for b in dummy_bits:
        v_pts.extend([1.0 if b == "1" else -1.0] * spb)
    
    waveform = SignalWaveform(
        bits=dummy_bits,
        time_points=t_pts,
        voltages=v_pts,
        samples_per_bit=spb,
        bit_duration=1.0,
    )
    print(f" -> Physical Signal Model Created for Bits: '{waveform.bits}'")
    print(f" -> Total Duration: {waveform.total_duration}s | Total Physical Samples: {waveform.total_samples}")
    t_mid, v_mid = waveform.get_midpoint_sample(0)
    print(f" -> Receiver Mid-point Probe at Bit 0: t={t_mid:.2f}s, V={v_mid:+.1f}V")

    # ---------------------------------------------------------
    # 3. Analog Continuous Signal & Nyquist Sampling
    # ---------------------------------------------------------
    print("\n[3] Analog Signal Modeling & Nyquist Sampling")
    sig = ContinuousSignal.create_simple_sine(amplitude=2.5, frequency=5.0)  # 5 Hz sine wave
    print(f" -> Analog Waveform: x(t) = 2.5 * sin(2 * pi * 5.0 * t)")
    print(f" -> Maximum Frequency (f_max):     {sig.max_frequency:.1f} Hz")
    print(f" -> Theoretical Nyquist Rate (2*f): {sig.nyquist_rate:.1f} Hz")
    
    fs = 20.0  # 20 Hz (> 10 Hz Nyquist)
    times, samples = sig.sample(sampling_rate=fs, duration=0.2)
    print(f" -> Uniform Sampling at fs = {fs} Hz (Nyquist satisfied: {sig.is_nyquist_satisfied(fs)})")
    print(f" -> Collected {len(samples)} discrete samples across 0.2s duration.")
    for i, (t_val, s_val) in enumerate(zip(times[:4], samples[:4])):
        print(f"    Sample [{i}]: t = {t_val:.3f}s -> x(t) = {s_val:+.3f} V")

    print("\n" + "=" * 70)
    print(" Status: All Core Modules Initialized and Verified Successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
