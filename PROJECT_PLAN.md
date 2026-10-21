# ITT 036: Digital Signal Encoder & Decoder — 2-Week Plan & 3-Person Team Division

---

## 1. 3-Person Division of Responsibilities (Modular Architecture)

To ensure that each team member has a cohesive, well-defined module to build, commit, and explain during the presentation/viva, the project is divided into **three balanced domains**:

```
+---------------------------------------------------------------------------------------------------------+
|                                        TEAM MEMBER RESPONSIBILITIES                                     |
+------------------------------------+------------------------------------+-------------------------------+
|  PERSON 1: Data & Algorithm Lead   |   PERSON 2: Line Coding & Decoder  |   PERSON 3: Analog DSP & GUI  |
|                                    |            (Extra Credit)          |         (Extra Credit)        |
+------------------------------------+------------------------------------+-------------------------------+
| * Digital Data Generator           | * Base Line Encoders:              | * Pulse Code Modulation (PCM):|
|   - Pure random bitstream          |   - NRZ-L, NRZ-I                   |   - Continuous analog waves   |
|   - Pattern-injected (4 & 8 zeros) |   - Manchester, Diff Manchester    |   - Nyquist sampling          |
|                                    |   - AMI (Alternate Mark Inversion) |   - Uniform quantization (2^n)|
| * Competitive Coding:              |                                    |   - Binary code assignment    |
|   - O(N) Manacher's Algorithm      | * Scrambling State Machines:       |                               |
|   - Benchmark vs O(N^2) naive      |   - B8ZS (000VB0VB replacement)    | * Delta Modulation (DM):      |
|                                    |   - HDB3 (000V / B00V parity)      |   - 1-bit comparator tracking |
| * System CLI & Orchestration:      |                                    |   - Staircase approximation   |
|   - CLI workflow controller        | * Physical Waveform Decoder (EC):  |   - Slope overload & noise    |
|   - Argument parsing & user prompts|   - Voltage sampling V(t)          |                               |
|   - Input validation & testing     |   - Clock & edge detection         | * Multi-Track GUI (EC):       |
|                                    |   - Violation de-scrambler         |   - Interactive GUI dashboard |
|                                    |                                    |   - Live parameter sliders    |
|                                    |                                    |   - PCM -> Line Code pipeline |
+------------------------------------+------------------------------------+-------------------------------+
```

---

### Detailed Breakdown by Person

#### 👤 Person 1: Data Stream Engineering & Algorithmic Optimization
- **Core Domain**: Digital generation, string algorithms, computational complexity, and main CLI pipeline.
- **Key Modules to Code**:
  - `src/generator/data_generator.cpp` (`include/generator/data_generator.hpp`): Generates pure random bit sequences of length $N$, as well as sequences injected with runs of 4 consecutive zeros (`0000`) and 8 consecutive zeros (`00000000`).
  - `src/algorithms/palindrome.cpp` (`include/algorithms/palindrome.hpp`): Implements **Manacher’s Algorithm** to achieve strict **$O(N)$ linear time complexity** for finding the longest palindromic substring (guaranteeing full marks for the competitive coding rubric without nested if/else statements).
  - `src/cli/menu.cpp` (`include/cli/menu.hpp`): Builds the interactive terminal menu that handles user prompts (analog vs digital selection, coding scheme choice, AMI scrambling queries, decode confirmation).
  - `benchmarks/benchmark_palindrome.cpp`: Benchmark script showing runtime comparison between $O(N)$ Manacher's and naive $O(N^2)$ checks.
- **Viva / Explanation Talking Points**:
  - *"I designed the data generation engine and solved the competitive coding challenge. Instead of an $O(N^2)$ expand-around-center approach, I implemented Manacher’s Algorithm which runs in $O(N)$ by maintaining the center and rightmost boundary of previously discovered palindromes, eliminating redundant character comparisons."*

---

#### 👤 Person 2: Line Coding Schemes, Bipolar Scrambling & Physical Signal Decoder
- **Core Domain**: Baseband transmission, signaling rules, synchronization, bipolar violations, and physical waveform-based decoding.
- **Key Modules to Code**:
  - `src/line_coding/base.cpp` (`include/line_coding/base.hpp`): Defines the `LineEncoder` interface and signal representation (voltages over discrete time intervals).
  - `src/line_coding/encoders.cpp` (`include/line_coding/encoders.hpp`): Implements **NRZ-L**, **NRZ-I**, **Manchester**, **Differential Manchester**, and **AMI**.
  - `src/scrambling/b8zs.cpp` & `src/scrambling/hdb3.cpp` (`include/scrambling/`): Implements state-machine scramblers for **B8ZS** and **HDB3** that track prior pulse polarity and pulse count parity without spaghetti if/else code.
  - `src/decoder/signal_decoder.cpp` (**Extra Credit**): Implements the physical line decoder that samples the analog voltage array $V(t)$ at bit mid-points, detects transition edges, distinguishes normal pulses from bipolar violations ($V$), and recovers the original digital stream.
- **Viva / Explanation Talking Points**:
  - *"I developed the line encoding and scrambling engines along with the physical signal decoder. For scrambling, I modeled B8ZS and HDB3 as formal finite state machines. For the extra credit decoder, rather than reading back digital memory, our receiver samples the physical voltage levels $V(t)$, tracks clock transitions, and detects deliberate bipolar violations ($V$) to seamlessly reconstruct the original bitstream."*

---

#### 👤 Person 3: Analog Modulation (PCM / DM), Staircase Decoder & Interactive GUI
- **Core Domain**: Continuous-to-discrete conversion, Nyquist sampling theory, quantization distortion, integrated signal pipeline, and graphical visualization.
- **Key Modules to Code**:
  - `src/analog/quantization.cpp` (`include/analog/quantization.hpp`): Implements **PCM** (continuous wave generation $A \sin(2\pi f t)$, Nyquist sampling $f_s \ge 2 f_{max}$, uniform quantization with $n$ bits / $L = 2^n$ levels, binary code mapping, and staircase DAC reconstruction).
  - `src/analog/delta_modulation.cpp` (`include/analog/delta_modulation.hpp`): Implements **Delta Modulation (DM)** with 1-bit quantization, configurable step size $\Delta$, staircase tracking, and slope overload/granular noise indicators.
  - `src/pipeline/bridge.cpp` (`include/pipeline/bridge.hpp`): Connects digitized PCM/DM output bitstreams directly into Person 2's line coding encoders.
  - `visualizer/index.html` & `app.js` (**Extra Credit**): Builds the rich interactive Web Oscilloscope Studio (multi-panel plot showing continuous wave, sampled pulses, quantized levels, binary bits, clock signal, encoded signal, and scrambled waveform with interactive sliders).
- **Viva / Explanation Talking Points**:
  - *"I developed the analog modulation subsystem (PCM and Delta Modulation) and the graphical user interface. I implemented Nyquist-rate sampling, uniform quantization, and DAC staircase reconstruction. I also created the bridge that pipes digitized analog bitstreams into our line encoders, and built the multi-track visual interface that displays all signals synchronously."*

---

## 2. 2-Week Day-by-Day Implementation Roadmap (14 Days)

Every team member has a concrete task and commit target every single day:

### Week 1: Core Systems, Algorithms & Line Coding

| Day | Date | 👤 Person 1 (Data & Algo) | 👤 Person 2 (Line Coding & Scrambling) | 👤 Person 3 (Analog DSP & Viz) |
| :---: | :---: | :--- | :--- | :--- |
| **Day 1** | Oct 06 | Initialize repo, `.gitignore`, directory layout, and pure random generator | Define `LineEncoder` base class and signal data structures ($t$, $V(t)$) | Setup C++20 build system, dependencies (GCC/Clang, Makefile), test framework |
| **Day 2** | Oct 07 | Implement pattern-injected generator (runs of 4 and 8 zeros) | Implement **NRZ-L** encoder with voltage mapping ($+V, -V$) | Build analog signal generator ($A \sin(2\pi f t)$, multi-tone) |
| **Day 3** | Oct 08 | Implement **Manacher's Algorithm** for $O(N)$ palindrome search | Implement **NRZ-I** encoder with differential transition tracking | Implement Nyquist sampling module ($f_s \ge 2 f_{max}$) |
| **Day 4** | Oct 09 | Add comprehensive unit tests & edge cases for Manacher's ($O(N)$) | Implement **Manchester** (IEEE 802.3 & Thomas conventions) | Implement uniform quantization ($L=2^n$ levels, step size $\Delta$) |
| **Day 5** | Oct 10 | Build benchmark script comparing $O(N)$ vs naive $O(N^2)$ | Implement **Differential Manchester** (boundary & mid-bit transitions) | Implement PCM binary encoder (natural binary / Gray code) |
| **Day 6** | Oct 11 | Begin CLI controller architecture and menu structure | Implement **AMI (Alternate Mark Inversion)** with alternating polarity | Implement PCM Decoder (reconstructed staircase signal) |
| **Day 7** | Oct 12 | **Week 1 Integration**: Connect Generator + Palindrome to CLI | Implement **B8ZS Scrambler** state machine ($000VB0VB$) | Build initial multi-track Matplotlib plotting module |

---

### Week 2: Scrambling, Decoding, Integration & UI Polish

| Day | Date | 👤 Person 1 (Data & Algo) | 👤 Person 2 (Line Coding & Scrambling) | 👤 Person 3 (Analog DSP & Viz) |
| :---: | :---: | :--- | :--- | :--- |
| **Day 8** | Oct 13 | Enhance CLI with AMI scrambling prompts and options | Implement **HDB3 Scrambler** state machine ($000V$ / $B00V$) | Implement **Delta Modulation (DM)** encoder & staircase tracker |
| **Day 9** | Oct 14 | Connect Analog PCM/DM input selection into main CLI | Unit tests for B8ZS and HDB3 state machines & violation tracking | Add slope overload and granular noise detection to DM |
| **Day 10** | Oct 15 | Build end-to-end integration test suite across all modules | Implement **Physical Signal Decoder** (mid-bit voltage sampling) | Build **Pipeline Bridge**: Feed PCM/DM bitstream to Line Encoders |
| **Day 11** | Oct 16 | Add input validation, error handling, and help documentation | Extend physical decoder to decode **Manchester & Diff Manchester** | Build interactive GUI window with waveform display tracks |
| **Day 12** | Oct 17 | Stress-test edge cases ($10^5$ bitstreams, random sequences) | Extend physical decoder for **AMI, B8ZS, and HDB3** de-scrambling | Add interactive sliders to GUI (frequency, amplitude, sampling rate) |
| **Day 13** | Oct 18 | Cross-verify all assignment requirements and rubric checklist | Integration test: verify waveform decoder accuracy $\ge 99.9\%$ | Add visual violation markers ($V$ and $B$) on GUI plots |
| **Day 14** | Oct 19 | Write **1-Page Specification Report** (Architecture & Complexity) | Write **Report Section** (Line Coding, Scrambling, Decoder math) | Write **Report Section** (PCM/DM theory, GUI guide, references) |

*(Days 20 & 21 serve as final buffer and practice presentation before Oct 21 submission).*

---

## 3. Git Collaboration & Daily Commit Strategy

To make sure everyone pushes code cleanly every day without conflicts:
1. **Branching Model**:
   - `main`: Production-ready, fully tested code.
   - `feature/person1-data-algo`: Person 1's active branch.
   - `feature/person2-line-coding`: Person 2's active branch.
   - `feature/person3-analog-gui`: Person 3's active branch.
2. **Daily Routine**:
   - Each member works in their dedicated directory (`src/generator`, `src/line_coding`, `src/analog`).
   - Run tests before pushing: `pytest tests/`.
   - Daily commit convention: `feat(scope): concise description of work done`.
   - Merge into `main` at the end of each day or milestone.
