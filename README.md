# Digital Signal Encoder & Decoder

Implementation of a digital signal transmission, modulation, and line coding system for **ITT 036 (Programming Assignment 1)**.

The project models the physical layer of digital communication, covering discrete data generation, baseband line coding, scrambling techniques, analog pulse modulation (PCM / Delta Modulation), and physical waveform decoding.

---

## Architecture & Features

### 1. Digital Data Generation (Person 1)
- **Random Sequence Generation**: Configurable pseudo-random binary stream generation with uniform bit distribution.
- **Pattern Injection**:
  - `generate_b8zs_stream(length, num_injections)`: Guaranteed runs of 8 consecutive zeros (`00000000`) for B8ZS scrambling validation.
  - `generate_hdb3_stream(length, num_injections)`: Guaranteed runs of 4 consecutive zeros (`0000`) for HDB3 scrambling validation.
  - `inject_pattern(base_stream, pattern, position, overwrite)`: Arbitrary binary pattern injection at deterministic or randomized positions.
- **Bitstream Analysis**: `find_zero_runs` and `max_consecutive_zeros` for stream property inspection.
- **Validation & Determinism**: Strict binary validation and seed support for reproducible test cases.

### 2. Physical Signal Modeling & NRZ-L Line Coding (Person 2)
- **Signal Waveform Model (`SignalWaveform`)**: Represents discrete-time physical voltage signals $V(t)$, tracking sample points, bit durations, nominal voltage levels ($+V, 0V, -V$), and mid-bit sampling points.
- **NRZ-L Encoder (`NRZLEncoder`)**:
  - Implements Non-Return-to-Zero-Level encoding with constant voltage over bit duration $T_b$.
  - Dual mapping conventions:
    - Standard Telecom: bit `'0'` $\to +V$, bit `'1'` $\to -V$.
    - Inverted Mapping: bit `'0'` $\to -V$, bit `'1'` $\to +V$.
  - Signal metrics: adjacent transition counts, transition density, and average DC bias ($\bar{V}$).
- **Physical Mid-Point Receiver Decoder**: Samples $V(t)$ at bit mid-points ($t = (i + 0.5) T_b$) and applies decision slicing to reconstruct the original bit sequence with 100% fidelity.

### 3. Continuous Analog Signal & Multi-Tone DSP (Person 3)
- **Single-Tone & Composite Multi-Tone (`ContinuousSignal`)**:
  - Continuous sinusoidal modeling: $x(t) = \sum A_k \sin(2\pi f_k t + \phi_k) + V_{DC}$.
  - Dual-tone signaling factory (e.g., DTMF telecommunication tones).
- **Harmonic Series Synthesis**:
  - Fourier series square wave approximation: $x(t) = \sum_{m=0}^{N-1} \frac{4A}{\pi (2m+1)} \sin(2\pi (2m+1) f_0 t)$.
  - Sawtooth Fourier approximation: $x(t) = \sum_{k=1}^N \frac{2A}{\pi k} \sin(2\pi k f_0 t)$.
- **Theoretical Signal Metrics**:
  - Normalized Average Power: $P_{avg} = V_{DC}^2 + \frac{1}{2} \sum A_k^2$.
  - Root-Mean-Square (RMS) voltage: $V_{rms} = \sqrt{P_{avg}}$.
  - Peak-to-Average Power Ratio (PAPR): $\frac{V_{peak}^2}{P_{avg}}$.
  - Maximum frequency $f_{\max}$ and bandwidth $B = f_{\max} - f_{\min}$.
- **Nyquist Rate Analysis & Sampling**:
  - Automatically calculates theoretical Nyquist rate ($f_{\text{nyquist}} = 2 f_{\max}$) and validates sampling satisfaction ($f_s \ge 2 f_{\max}$).
  - Discrete uniform time-domain sampling for PCM and Delta Modulation.
  - High-resolution waveform generation and Matplotlib visualizer utility (`plot_continuous_and_sampled`).

---

## Project Structure

```text
DC-assignment/
├── PROJECT_PLAN.md               # 2-Week day-by-day implementation roadmap
├── README.md                     # Project overview and system documentation
├── requirements.txt              # Dependencies (numpy, matplotlib, pytest)
├── main.py                       # System verification script
├── src/
│   ├── __init__.py
│   ├── generator/                # [Person 1] Digital bitstream generation
│   │   ├── __init__.py
│   │   └── data_generator.py     # Random & pattern-injected generator
│   ├── line_coding/              # [Person 2] Line coding and signal models
│   │   ├── __init__.py
│   │   ├── base.py               # LineEncoder base class & SignalWaveform
│   │   └── encoders.py           # NRZ-L encoder & receiver decoder
│   └── analog/                   # [Person 3] Continuous signals and sampling
│       ├── __init__.py
│       ├── continuous_signal.py  # Single/multi-tone modeling & harmonics
│       └── plotter.py            # Waveform visualization utility
└── tests/
    ├── __init__.py
    ├── test_generator.py         # Bitstream generator & pattern tests
    ├── test_base_encoder.py      # Signal waveform model tests
    ├── test_nrz_l.py             # NRZ-L line coding & decoding tests
    └── test_continuous_signal.py # Multi-tone analog & Nyquist tests
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
