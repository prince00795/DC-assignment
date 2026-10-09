# Digital Signal Encoder & Decoder

Implementation of a digital signal transmission, modulation, and line coding system for **ITT 036 (Programming Assignment 1)**.

The project models the physical layer of digital communication, covering discrete data generation, competitive string algorithms, baseband line coding, scrambling techniques, analog pulse modulation (PCM / Delta Modulation), and physical waveform decoding.

---

## Architecture & Features

### 1. Digital Data Generation & Algorithmic Optimization (Person 1)
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

### 2. Physical Signal Modeling & Line Coding Schemes (Person 2)
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

### 3. Continuous Analog Signal & Nyquist Sampling (Person 3)
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

---

## Project Structure

```text
DC-assignment/
├── PROJECT_PLAN.md               # 2-Week day-by-day implementation roadmap
├── README.md                     # Project overview and system documentation
├── requirements.txt              # Dependencies (numpy, matplotlib, pytest)
├── main.py                       # Milestone system verification script
├── src/
│   ├── __init__.py
│   ├── algorithms/               # [Person 1] Algorithmic optimizations
│   │   ├── __init__.py
│   │   └── palindrome.py         # Manacher's O(N) palindrome search & naive baseline
│   ├── generator/                # [Person 1] Digital bitstream generation
│   │   ├── __init__.py
│   │   └── data_generator.py     # Random & pattern-injected generator (B8ZS/HDB3)
│   ├── line_coding/              # [Person 2] Line coding and signal models
│   │   ├── __init__.py
│   │   ├── base.py               # LineEncoder base class & SignalWaveform model
│   │   └── encoders.py           # NRZ-L & NRZ-I encoders & physical decoders
│   └── analog/                   # [Person 3] Continuous signals and sampling
│       ├── __init__.py
│       ├── continuous_signal.py  # Single/multi-tone modeling & Fourier harmonics
│       ├── sampling.py           # Nyquist sampling engine & Whittaker-Shannon sinc reconstruction
│       └── plotter.py            # Waveform visualization utilities
└── tests/
    ├── __init__.py
    ├── test_generator.py         # Bitstream generator & pattern injection tests
    ├── test_palindrome.py        # Manacher's O(N) algorithm & fuzz validation tests
    ├── test_base_encoder.py      # Signal waveform data model tests
    ├── test_nrz_l.py             # NRZ-L line coding & decoding tests
    ├── test_nrz_i.py             # NRZ-I differential coding & decoding tests
    ├── test_continuous_signal.py # Multi-tone analog & Fourier harmonic tests
    └── test_sampling.py          # Nyquist sampling, aliasing & sinc reconstruction tests
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
