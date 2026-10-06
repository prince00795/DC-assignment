# Digital Signal Encoder & Decoder

Implementation of a digital signal transmission, modulation, and line coding system for **ITT 036 (Programming Assignment 1)**.

The project models the physical layer of digital communication, covering discrete data generation, baseband line coding, scrambling techniques, analog pulse modulation (PCM / Delta Modulation), and signal parameter decoding.

---

## Features Implemented

### 1. Digital Data Generation
- **Random Sequence Generation**: Configurable pseudo-random binary stream generation with uniform bit distribution.
- **Pattern Injection**: Injects specific runs of consecutive zeros (e.g., 4 consecutive zeros for HDB3, 8 consecutive zeros for B8ZS) at non-overlapping positions to test scrambling mechanisms.
- **Validation**: Strict binary validation and seed support for reproducible test cases.

### 2. Physical Signal Modeling & Line Coding Framework
- **Signal Waveform Model (`SignalWaveform`)**: Represents discrete-time physical voltage signals $V(t)$, tracking sample points, bit durations, nominal voltage levels ($+V, 0V, -V$), and mid-bit sampling points.
- **Line Coding Architecture (`LineEncoder`)**: Extensible abstract base class establishing a consistent encoding interface for NRZ, Manchester, and AMI schemes.

### 3. Continuous Analog Signal & Sampling
- **Analog Signal Generator (`ContinuousSignal`)**: Generates continuous sinusoidal signals $x(t) = A \sin(2\pi f t + \phi) + \text{offset}$ and composite multi-tone harmonics.
- **Nyquist Rate Analysis**: Automatically calculates maximum frequency $f_{\max}$ and theoretical Nyquist sampling rate ($f_{\text{nyquist}} = 2 f_{\max}$).
- **Uniform Time-Domain Sampling**: Generates discrete sample pairs $(t_k, x(t_k))$ for digitization via PCM and Delta Modulation.

---

## Project Structure

```text
DC-assignment/
├── README.md                     # Project overview and instructions
├── requirements.txt              # Dependencies
├── main.py                       # System verification script
├── src/
│   ├── __init__.py
│   ├── generator/                # Digital bitstream generation
│   │   ├── __init__.py
│   │   └── data_generator.py
│   ├── line_coding/              # Line coding and signal models
│   │   ├── __init__.py
│   │   └── base.py
│   └── analog/                   # Continuous signals and sampling
│       ├── __init__.py
│       └── continuous_signal.py
└── tests/
    ├── __init__.py
    ├── test_generator.py         # Bitstream generator tests
    ├── test_base_encoder.py      # Signal model tests
    └── test_continuous_signal.py # Analog sampling tests
```

---

## Setup & Execution

### Prerequisites
- Python 3.9+

### Run System Verification
```bash
python3 main.py
```

### Run Test Suite
```bash
python3 -m unittest discover -s tests -v
```
