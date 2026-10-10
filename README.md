# Digital Signal Encoder & Decoder System

Implementation of a digital signal transmission, modulation, and baseband line coding system for **ITT 036 (Programming Assignment 1)**.

The project models the physical and transport layers of digital communication, covering discrete data generation, competitive string algorithms, baseband line coding, scrambling techniques, analog pulse code modulation (PCM), uniform quantization, and physical waveform decoding.

---

## Architecture & Subsystems

### 1. Digital Data Stream Engineering & Algorithmic Optimization
- **Random Sequence Generation**: Configurable pseudo-random binary stream generation with uniform bit distribution.
- **Pattern Injection**:
  - `generate_b8zs_stream(length, num_injections)`: Guaranteed runs of 8 consecutive zeros (`00000000`) for B8ZS scrambling validation.
  - `generate_hdb3_stream(length, num_injections)`: Guaranteed runs of 4 consecutive zeros (`0000`) for HDB3 scrambling validation.
  - `inject_pattern(base_stream, pattern, position, overwrite)`: Arbitrary binary pattern injection at deterministic or randomized positions.
- **Bitstream Analysis**: `find_zero_runs` and `max_consecutive_zeros` for stream property inspection.
- **Manacher's Algorithm ($O(N)$ Palindromic Search)** (`src/algorithms/palindrome.py`):
  - Strictly **linear time $O(N)$** longest palindromic substring discovery in arbitrary sequences and digital bitstreams.
  - Intersperses boundary characters (`#`) with terminal sentinels (`^`, `$`) to handle even and odd palindromes uniformly.
  - Maintains center and rightmost boundary references ($C, R$) to eliminate redundant character comparisons.
  - Outperforms naive $O(N^2)$ expand-around-center checks while preserving identical output accuracy.
  - Stress-tested on large strings ($10^4+$ characters) and worst-case repeated patterns.

### 2. Baseband Physical Line Coding & Receiver Decoders
- **Signal Waveform Model (`SignalWaveform`)**: Represents discrete-time physical voltage signals $V(t)$, tracking sample points, bit durations, nominal voltage levels ($+V, 0V, -V$), and mid-bit sampling points.
- **NRZ-L Encoder & Decoder (`NRZLEncoder`)**:
  - Non-Return-to-Zero-Level encoding with constant voltage over bit duration $T_b$.
  - Standard Telecom (0 $\to +V$, 1 $\to -V$) and Inverted (0 $\to -V$, 1 $\to +V$) conventions.
  - Mid-point receiver probing ($t = (i + 0.5) T_b$) with decision slicing.
- **NRZ-I Encoder & Differential Decoder (`NRZIEncoder`)**:
  - Non-Return-to-Zero-Invert differential signaling:
    - Standard Telecom: bit `'1'` triggers voltage inversion ($+V \leftrightarrow -V$), bit `'0'` maintains constant level.
    - Inverted Mode: bit `'0'` triggers voltage inversion, bit `'1'` maintains level.
  - Differential transition tracking: records transition indices, counts, and transition density.
  - Differential receiver decoder: probes mid-bit voltage levels and compares adjacent intervals to reconstruct the original stream with 100% fidelity without polarity ambiguity.
- **Manchester Biphase Encoder & Decoder (`ManchesterEncoder`)**:
  - Biphase line coding with guaranteed mid-bit transitions on every bit interval for clock recovery and zero net DC bias.
  - **IEEE 802.3 Standard (Ethernet 10BASE-T)**:
    - Bit `'0'`: High-to-Low transition ($+V \to -V$).
    - Bit `'1'`: Low-to-High transition ($-V \to +V$).
  - **G.E. Thomas Convention**:
    - Bit `'0'`: Low-to-High transition ($-V \to +V$).
    - Bit `'1'`: High-to-Low transition ($+V \to -V$).
  - Boundary transition tracking between consecutive identical bits.
  - Physical receiver decoding by probing quarter-points ($0.25 T_b$) and three-quarter points ($0.75 T_b$) to detect edge direction.
  - Signal violation detection for un-transitioned or corrupt intervals.

### 3. Analog Continuous DSP, Nyquist Sampling & Uniform PCM Quantization
- **Continuous Multi-Tone Modeling (`ContinuousSignal`)**:
  - Continuous sinusoidal modeling: $x(t) = \sum A_k \sin(2\pi f_k t + \phi_k) + V_{DC}$.
  - Dual-tone signaling factory (e.g., DTMF telecommunication tones).
  - Fourier series harmonic synthesis (Square wave and Sawtooth approximations).
  - Signal metrics: Normalized Average Power, RMS Voltage, PAPR, maximum frequency $f_{\max}$, and bandwidth.
- **Nyquist-Shannon Sampling Engine (`NyquistSampler`)**:
  - Nyquist criterion verification: $f_s \ge 2 f_{\max}$.
  - Sampling Modes:
    - **Ideal Impulse Sampling**: $x_s[n] = x(n T_s)$.
    - **Flat-Top / Zero-Order Hold (ZOH)**: Pulse amplitude modulation holding voltage level across bit intervals.
    - **Natural Sampling**: Gated periodic pulses of finite width $\tau$.
  - **Spectral Folding & Aliasing Analysis**:
    - Detects under-sampling and computes baseband folded alias frequencies: $f_{\text{alias}} = \min(f \pmod{f_s}, f_s - (f \pmod{f_s}))$.
  - **Whittaker-Shannon Reconstruction (Sinc Interpolation)**:
    - Reconstructs continuous waveforms from discrete samples: $\hat{x}(t) = \sum x[n] \cdot \text{sinc}\left(\frac{t - n T_s}{T_s}\right)$.
    - Evaluates Mean Squared Error (MSE), RMSE, Max Error, and SNR (dB), demonstrating near-perfect reconstruction when $f_s \ge 2 f_{\max}$ vs distortion under sub-Nyquist rates.
  - High-resolution Matplotlib visualizers: `plot_continuous_and_sampled` and `plot_nyquist_reconstruction`.
- **Uniform PCM Quantization & Binary Codec (`UniformQuantizer`)**:
  - Quantizes continuous amplitude samples into $L = 2^n$ discrete representation levels for $n$-bit resolution.
  - Uniform step size: $\Delta = \frac{V_{\max} - V_{\min}}{2^n}$.
  - Mid-rise and Mid-tread quantization partition models.
  - Binary codeword mappings:
    - Natural binary (offset binary).
    - Gray coding (adjacent level Hamming distance of 1 to minimize transmission bit error impact).
    - Two's complement representation.
  - Error and noise metrics:
    - Max quantization error bounded by $|e| \le \frac{\Delta}{2}$.
    - Quantization noise power ($P_Q$) compared against theoretical value $\frac{\Delta^2}{12}$.
    - Empirical and theoretical Signal-to-Quantization-Noise Ratio (SQNR $\approx 6.02 n + 1.76$ dB).
  - Serialization into binary PCM bitstreams and DAC dequantization reconstruction.

---

## Project Structure

```text
DC-assignment/
├── PROJECT_PLAN.md               # 2-Week day-by-day implementation roadmap
├── README.md                     # Project overview and system documentation
├── requirements.txt              # Dependencies (numpy, matplotlib, pytest)
├── main.py                       # Integrated pipeline verification script
├── src/
│   ├── __init__.py
│   ├── algorithms/               # Algorithmic optimizations
│   │   ├── __init__.py
│   │   └── palindrome.py         # Manacher's O(N) palindrome search & naive baseline
│   ├── generator/                # Digital bitstream generation
│   │   ├── __init__.py
│   │   └── data_generator.py     # Random & pattern-injected generator (B8ZS/HDB3)
│   ├── line_coding/              # Baseband line coding and signal models
│   │   ├── __init__.py
│   │   ├── base.py               # LineEncoder base class & SignalWaveform model
│   │   └── encoders.py           # NRZ-L, NRZ-I, and Manchester encoders & decoders
│   └── analog/                   # Continuous signals, sampling, and quantization
│       ├── __init__.py
│       ├── continuous_signal.py  # Single/multi-tone modeling & Fourier harmonics
│       ├── sampling.py           # Nyquist sampling engine & Whittaker-Shannon sinc reconstruction
│       ├── quantization.py       # Uniform PCM quantizer & binary codeword encoding
│       └── plotter.py            # Waveform visualization utilities
└── tests/
    ├── __init__.py
    ├── test_generator.py         # Bitstream generator & pattern injection tests
    ├── test_palindrome.py        # Manacher's O(N) algorithm & fuzz validation tests
    ├── test_base_encoder.py      # Signal waveform data model tests
    ├── test_nrz_l.py             # NRZ-L line coding & decoding tests
    ├── test_nrz_i.py             # NRZ-I differential coding & decoding tests
    ├── test_manchester.py        # Manchester IEEE 802.3 and Thomas line coding tests
    ├── test_continuous_signal.py # Multi-tone analog & Fourier harmonic tests
    ├── test_sampling.py          # Nyquist sampling, aliasing & sinc reconstruction tests
    └── test_quantization.py      # Uniform PCM quantization, SQNR & Gray code tests
```

---

## Setup & Execution

### Prerequisites
- Python 3.9+

### Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run System Verification
```bash
python3 main.py
```

### Run Test Suite
```bash
# Using pytest
pytest tests/ -v

# Or using standard unittest
python3 -m unittest discover -s tests -v
```
