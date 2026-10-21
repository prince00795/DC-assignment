# Digital Signal Transmission, Modulation & Line Coding System
### ITT 036: Digital Communication System Engineering — Final Submission Repository

[![Language](https://img.shields.io/badge/Language-C%2B%2B20-blue.svg)]()
[![Standards](https://img.shields.io/badge/Standards-IEEE%20802.3%20%7C%20802.5%20%7C%20ITU--T%20G.703-orange.svg)]()
[![Compiler](https://img.shields.io/badge/Compiler-GCC%20%7C%20Clang%20%7C%20MSVC-informational.svg)]()
[![Decoder Accuracy](https://img.shields.io/badge/Decoder%20Accuracy-100.00%25%20(%E2%89%A599.9%25)-success.svg)]()
[![Manacher Complexity](https://img.shields.io/badge/Algorithm-O(N)%20Strict%20Linear-blueviolet.svg)]()
[![Test Suite](https://img.shields.io/badge/Tests-94%20%2F%2094%20Passing%20(100%25)-brightgreen.svg)]()

---

## 👩‍🏫 Quick 60-Second Evaluator Guide

Welcome, Evaluator! To rapidly test and run this project, use one of the verification paths below:

| Verification Goal | macOS / Linux Terminal | Windows (CMD or PowerShell) | Expected Result |
| :--- | :--- | :--- | :--- |
| **1. Zero-Install Visual Studio (Instant)** | `open index.html` | Double-click `open_visualizer.bat` *(or `index.html`)* | Launches interactive Oscilloscope Studio with live sliders & Web Audio sonification |
| **2. Run All Automated Tests** | `make test` | `.\build.ps1 test` *(or `.\bin\run_tests.exe`)* | **`94 / 94 passed (100% SUCCESS)`** |
| **3. Live System Specification Audit** | `./bin/dc_system --audit` | `.\bin\dc_system.exe --audit` | Live quantitative report showing **100.00% decoding accuracy** |
| **4. Palindrome $O(N)$ Benchmark** | `make benchmark` | `.\build.ps1 benchmark` | Displays timing table comparing $O(N)$ Manacher vs $O(N^2)$ Naive |
| **5. Interactive Menu System** | `./bin/dc_system` | `.\bin\dc_system.exe` | Interactive console menu for custom stream testing (Options 1–9) |

---

## 🛠️ Build & Compilation Instructions

### Prerequisites
- Any standard C++20 compiler: **GCC 11+**, **Clang 13+**, or **MSVC 2019+**.
- Optional: `make` (macOS/Linux) or PowerShell (Windows).

### Compilation Options

#### Option 1: macOS / Linux (using Makefile)
```bash
# 1. Compile everything (CLI, tests, and benchmark)
make all

# 2. Run test suite
make test

# 3. Run palindrome benchmark
make benchmark
```

#### Option 2: Windows (using PowerShell script)
```powershell
# 1. Compile everything
.\build.ps1 all

# 2. Run test suite
.\build.ps1 test
.\bin\run_tests.exe

# 3. Run palindrome benchmark
.\build.ps1 benchmark
.\bin\benchmark.exe
```

#### Option 3: Direct Single-Command Compilation (Any OS with GCC/Clang)
```bash
g++ -std=c++20 -O2 -Wall -Wextra -Iinclude src/algorithms/*.cpp src/generator/*.cpp src/line_coding/*.cpp src/scrambling/*.cpp src/decoder/*.cpp src/analog/*.cpp src/pipeline/*.cpp src/cli/*.cpp src/main.cpp -o bin/dc_system
```

---

## 💻 Running the Programs & Verifying Output

### 1. Live System Specification Audit
Runs the entire transmission pipeline and verifies 100% accuracy, BER, SQNR, and algorithm bounds:
```bash
# macOS / Linux:
./bin/dc_system --audit

# Windows:
.\bin\dc_system.exe --audit
```

**Verified Terminal Output:**
```text
==============================================================================
 ITT 036: DAY 14 SPECIFICATION AUDIT & LIVE SUBSYSTEM METRICS (C++20)
==============================================================================
[Audit Stream] 101100100000000100001 (Length: 21 bits)

1. BASEBAND LINE CODING ACCURACY AUDIT:
------------------------------------------------------------------------------
Scheme                      Samples/Bit    Accuracy       BER         Status
------------------------------------------------------------------------------
NRZ-L                       100            100%           0.0000      [PASS]
NRZ-I                       100            100%           0.0000      [PASS]
Manchester (IEEE)           100            100%           0.0000      [PASS]
Manchester (Thomas)         100            100%           0.0000      [PASS]
Diff Manchester             100            100%           0.0000      [PASS]
AMI (Bipolar)               100            100%           0.0000      [PASS]

2. SCRAMBLING STATE MACHINE & VIOLATION AUDIT:
------------------------------------------------------------------------------
  B8ZS 8-Zero Scrambler:  Substitutions=1 | Violations=2 | Recovery=100% MATCH [PASS]
  HDB3 4-Zero Scrambler:  Substitutions=3 | Violations=3 | Recovery=100% MATCH [PASS]

3. COMPETITIVE STRING ALGORITHM: MANACHER O(N) LINEAR BENCHMARK:
------------------------------------------------------------------------------
  Bitstream N=1000   | Longest Palindrome=28  | Time=0.036 ms [Strict O(N)]
  Bitstream N=10000  | Longest Palindrome=28  | Time=0.313 ms [Strict O(N)]
  Bitstream N=50000  | Longest Palindrome=30  | Time=1.466 ms [Strict O(N)]

4. ANALOG MODULATION, NYQUIST SAMPLING & DELTA MODULATION AUDIT:
------------------------------------------------------------------------------
  Analog Multi-tone:      f_max = 4.0 Hz | Theoretical Nyquist = 8.000 Hz
  Sampling Performance:   fs = 20.0 Hz (2.500x Nyquist) | Sinc Recon SNR = 34.0 dB
  Uniform PCM (4-bit):    Theoretical SQNR = 25.8 dB | Empirical SQNR = 21.6 dB
  Delta Modulation (DM):  1-Bit Tracking SNR = 3.2 dB | Overload Indices = 15
==============================================================================
 SYSTEM AUDIT SUMMARY: ALL SUBSYSTEM SPECIFICATIONS FULLY SATISFIED [100%]
==============================================================================
```

---

### 2. Interactive Terminal Console Menu
Test any custom bitstream with immediate step-by-step visual feedback:
```bash
# macOS / Linux:
./bin/dc_system

# Windows:
.\bin\dc_system.exe
```

**Main Menu Navigation:**
```text
  [1] Digital Data Stream Generator (Random, 4/8-Zero Injected, Custom)
  [2] Competitive String Coding: Manacher's O(N) Palindromic Search
  [3] Baseband Line Coding (NRZ-L, NRZ-I, Manchester, Diff Manchester, AMI)
  [4] Scrambling State Machines: B8ZS & HDB3 with Violation Inspection
  [5] Analog Modulation: Continuous Wave, Nyquist Sampling & Uniform PCM
  [6] Delta Modulation (DM): 1-Bit Tracking, Slope Overload & Noise
  [7] Full End-to-End Integrated Transmission Pipeline
  [8] System Help & Architectural Documentation
  [9] Launch Interactive Visualizer & Oscilloscope Studio (Browser)
  [0] Exit
```

---

### 3. Automated C++ Unit & Integration Test Suite
Executes 94 comprehensive assertions verifying edge cases, boundary conditions, and stress tolerance:
```bash
# macOS / Linux:
make test

# Windows:
.\bin\run_tests.exe
```

**Output:**
```text
======================================================
 RUNNING C++20 DIGITAL COMMUNICATIONS TEST SUITE
======================================================
------------------------------------------------------
 Test Results: 94 / 94 passed (100% SUCCESS)
======================================================
```

---

### 4. Interactive Web Oscilloscope Studio & Sonification Lab
A complete browser-based digital communications laboratory:

```bash
# macOS:
open index.html

# Windows:
Double-click open_visualizer.bat (or open index.html in Chrome/Edge)

# Linux:
xdg-open visualizer/index.html
```

**Features Available in the Web Studio:**
1. **Interactive Multi-Track Oscilloscope**: Real-time synchronized rendering of Clock, NRZ-L, NRZ-I, Manchester (IEEE & Thomas), Differential Manchester, AMI, B8ZS, and HDB3 with hover voltage probe tooltip.
2. **Color-Coded Violation Markers**:
   - 🔴 **Red Markers**: Intentional Bipolar Violations ($V$).
   - 🟢 **Green Markers**: Bipolar Conforming Replacement Marks ($B$).
   - 🟠 **Orange Markers**: Receiver clock transitions.
3. **Analog DSP & Nyquist Lab**: Sliders for dual-tone frequencies ($f_1, f_2$), Nyquist sampling rate indicator ($f_s \ge 2 f_{\max}$), Whittaker-Shannon Sinc reconstruction, Uniform PCM staircase ($2^n$ levels), and Delta Modulation slope overload detector.
4. **Web Audio Sonification**: Click **"Listen to Signal"** to hear synthesized analog signals and quantized waveforms through your computer speakers!
5. **Manacher's $O(N)$ Palindrome Studio**: Visual preprocessed string $T$, radii array $P[i]$, centers, and maximal palindromic spans.

---

## 📁 Repository File Layout

```text
DC-assignment/
├── include/                     # Strictly typed C++20 Header Files
│   ├── algorithms/              # Manacher's O(N) Palindrome Search
│   ├── generator/               # Random & Pattern-Injected Bitstream Generator
│   ├── line_coding/             # Base Waveform & Line Coding Encoders
│   ├── scrambling/              # B8ZS & HDB3 Bipolar Scramblers
│   ├── decoder/                 # Physical Signal Waveform Slicing Decoder
│   ├── analog/                  # Continuous Signal, Nyquist Sampling, PCM, DM, Plotter
│   ├── pipeline/                # Integrated Transmission Pipeline Bridge
│   └── cli/                     # Interactive CLI Controller & Audit Reporter
├── src/                         # C++ Source Files (1:1 matching include/ structure)
├── tests/                       # Automated Test Suite (94 unit & integration tests)
│   └── test_runner.cpp
├── benchmarks/                  # Palindrome Complexity Benchmark
│   └── benchmark_palindrome.cpp
├── visualizer/                  # Web Oscilloscope Studio & Sonification Lab
│   ├── index.html
│   ├── app.js
│   └── style.css
├── bin/                         # Compiled binaries (dc_system, run_tests, benchmark)
├── Makefile                     # Standard Makefile (macOS / Linux / MSYS2)
├── build.ps1                    # PowerShell Build Script (Windows)
├── open_visualizer.bat          # 1-Click Visualizer Launcher (Windows)
├── open_visualizer.ps1          # PowerShell Visualizer Launcher (Windows)
├── index.html                   # Root launcher redirect to visualizer studio
└── README.md                    # Master submission document
```
