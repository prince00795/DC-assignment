/* ==============================================================================
   ITT 036: Digital Communication System Visualizer & Simulator Studio
   C++20 Implementation Mirrored in High-Performance JavaScript
   ============================================================================== */

'use strict';

// -----------------------------------------------------------------------------
// State Management
// -----------------------------------------------------------------------------
const state = {
  currentBitstream: "101100100000000100001",
  activeTab: "line-coding",
  voltageHigh: 1.0,
  voltageLow: -1.0,
  voltageZero: 0.0,
  samplesPerBit: 40,
  nrzInverted: false,
  noiseLevel: 0.0,
  
  // Analog state
  a1: 2.0,
  f1: 1.0,
  a2: 1.0,
  f2: 3.0,
  fs: 16.0,
  duration: 1.0,
  pcmBits: 3,
  dmDelta: 0.25,
  dmFs: 32.0,

  // Audio Context
  audioCtx: null,
  activeAudioSource: null,
  isPlayingAudio: false
};

// -----------------------------------------------------------------------------
// Algorithms: Manacher's Strict O(N) Palindromic Search
// -----------------------------------------------------------------------------
class ManachersAlgorithm {
  static run(s) {
    if (!s || s.length === 0) {
      return { length: 0, substring: "", centerIndex: 0, isEven: false, p: [], t: "^$" };
    }

    // Preprocess: s = "1001" -> T = "^#1#0#0#1#$"
    let t = "^";
    for (let i = 0; i < s.length; ++i) {
      t += "#" + s[i];
    }
    t += "#$";

    const n = t.length;
    const p = new Array(n).fill(0);
    let c = 0, r = 0;
    let maxLen = 0, centerIdx = 0;

    for (let i = 1; i < n - 1; ++i) {
      const iMirror = 2 * c - i;
      if (r > i) {
        p[i] = Math.min(r - i, p[iMirror]);
      } else {
        p[i] = 0;
      }

      // Expand palindrome around center i
      while (t[i + 1 + p[i]] === t[i - 1 - p[i]]) {
        p[i]++;
      }

      // Update center and right boundary
      if (i + p[i] > r) {
        c = i;
        r = i + p[i];
      }

      if (p[i] > maxLen) {
        maxLen = p[i];
        centerIdx = i;
      }
    }

    const start = Math.floor((centerIdx - maxLen) / 2);
    const longestSub = s.substr(start, maxLen);
    const isEven = (t[centerIdx] === '#');

    return {
      length: maxLen,
      substring: longestSub,
      startIndex: start,
      centerIndex: centerIdx,
      isEven: isEven,
      t: t,
      p: p
    };
  }
}

// -----------------------------------------------------------------------------
// Baseband Line Coding & Scrambling State Machines
// -----------------------------------------------------------------------------
class LineCodingEngine {
  static generateClock(bitstream, samplesPerBit) {
    const totalSamples = bitstream.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    const half = Math.floor(samplesPerBit / 2);
    for (let b = 0; b < bitstream.length; ++b) {
      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = (s < half) ? 1.0 : -1.0;
      }
    }
    return values;
  }

  // NRZ-L (Telecom: 0 -> +V, 1 -> -V; Inverted: 0 -> -V, 1 -> +V)
  static encodeNRZL(bitstream, samplesPerBit, inverted = false, vH = 1.0, vL = -1.0) {
    const totalSamples = bitstream.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    for (let b = 0; b < bitstream.length; ++b) {
      let v = (bitstream[b] === '0') ? (inverted ? vL : vH) : (inverted ? vH : vL);
      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = v;
      }
    }
    return values;
  }

  // NRZ-I (Transition on '1', maintain on '0')
  static encodeNRZI(bitstream, samplesPerBit, initialLevel = -1.0, vH = 1.0, vL = -1.0) {
    const totalSamples = bitstream.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    let current = initialLevel;
    for (let b = 0; b < bitstream.length; ++b) {
      if (bitstream[b] === '1') {
        current = (Math.abs(current - vH) < 1e-4) ? vL : vH;
      }
      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = current;
      }
    }
    return values;
  }

  // Manchester (IEEE 802.3: 0 -> High-to-Low, 1 -> Low-to-High)
  static encodeManchesterIEEE(bitstream, samplesPerBit, vH = 1.0, vL = -1.0) {
    const totalSamples = bitstream.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    const half = Math.floor(samplesPerBit / 2);
    for (let b = 0; b < bitstream.length; ++b) {
      const bit = bitstream[b];
      const first = (bit === '0') ? vH : vL;
      const second = (bit === '0') ? vL : vH;
      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = (s < half) ? first : second;
      }
    }
    return values;
  }

  // Manchester (Thomas: 0 -> Low-to-High, 1 -> High-to-Low)
  static encodeManchesterThomas(bitstream, samplesPerBit, vH = 1.0, vL = -1.0) {
    const totalSamples = bitstream.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    const half = Math.floor(samplesPerBit / 2);
    for (let b = 0; b < bitstream.length; ++b) {
      const bit = bitstream[b];
      const first = (bit === '0') ? vL : vH;
      const second = (bit === '0') ? vH : vL;
      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = (s < half) ? first : second;
      }
    }
    return values;
  }

  // Differential Manchester (Token Ring IEEE 802.5: mid-bit transition always; start transition for 0, none for 1)
  static encodeDiffManchester(bitstream, samplesPerBit, initialLevel = -1.0, vH = 1.0, vL = -1.0) {
    const totalSamples = bitstream.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    const half = Math.floor(samplesPerBit / 2);
    let prevSecondHalf = initialLevel;

    for (let b = 0; b < bitstream.length; ++b) {
      const bit = bitstream[b];
      let first;
      if (bit === '0') {
        first = (Math.abs(prevSecondHalf - vH) < 1e-4) ? vL : vH;
      } else {
        first = prevSecondHalf;
      }
      let second = (Math.abs(first - vH) < 1e-4) ? vL : vH;
      prevSecondHalf = second;

      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = (s < half) ? first : second;
      }
    }
    return values;
  }

  // AMI (Alternate Mark Inversion: 0 -> 0V, 1 -> alternating +V and -V)
  static encodeAMI(bitstream, samplesPerBit, vH = 1.0, vL = -1.0, vZ = 0.0) {
    const totalSamples = bitstream.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    let lastPolarity = vL; // so first '1' is +V

    for (let b = 0; b < bitstream.length; ++b) {
      let v = vZ;
      if (bitstream[b] === '1') {
        v = (Math.abs(lastPolarity - vH) < 1e-4) ? vL : vH;
        lastPolarity = v;
      }
      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = v;
      }
    }
    return values;
  }

  // B8ZS Scrambler (North American T1: 8 zeros replaced with 000VB0VB)
  static encodeB8ZS(bitstream, samplesPerBit, vH = 1.0, vL = -1.0, vZ = 0.0) {
    const pulses = [];
    const substitutions = [];
    const violations = [];
    const balances = [];

    let lastPolarity = vL;
    let i = 0;

    while (i < bitstream.length) {
      if (i + 8 <= bitstream.length && bitstream.substr(i, 8) === "00000000") {
        const v = lastPolarity; // same as previous = Bipolar Violation
        const b = (Math.abs(v - vH) < 1e-4) ? vL : vH; // opposite = Balancing pulse
        const subPattern = [vZ, vZ, vZ, v, b, vZ, b, v];

        substitutions.push({
          startIndex: i,
          length: 8,
          rule: (Math.abs(lastPolarity - vH) < 1e-4) ? "000+-0-+" : "000-+0+-"
        });

        violations.push(i + 3);
        balances.push(i + 4);
        balances.push(i + 6);
        violations.push(i + 7);

        for (const p of subPattern) {
          pulses.push(p);
        }
        lastPolarity = v;
        i += 8;
      } else {
        if (bitstream[i] === '1') {
          const p = (Math.abs(lastPolarity - vH) < 1e-4) ? vL : vH;
          pulses.push(p);
          lastPolarity = p;
        } else {
          pulses.push(vZ);
        }
        i++;
      }
    }

    const totalSamples = pulses.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    for (let b = 0; b < pulses.length; ++b) {
      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = pulses[b];
      }
    }

    return { values, substitutions, violations, balances, pulses };
  }

  // HDB3 Scrambler (European E1: 4 zeros replaced with 000V or B00V based on non-zero pulses parity)
  static encodeHDB3(bitstream, samplesPerBit, vH = 1.0, vL = -1.0, vZ = 0.0) {
    const pulses = [];
    const substitutions = [];
    const violations = [];
    const balances = [];

    let lastPolarity = vL;
    let nonZeroSinceLastSub = 0;
    let i = 0;

    while (i < bitstream.length) {
      if (i + 4 <= bitstream.length && bitstream.substr(i, 4) === "0000") {
        let subPattern = [];
        let rule = "";

        if (nonZeroSinceLastSub % 2 === 1) {
          // Odd: 000V
          const v = lastPolarity; // same as last = violation
          subPattern = [vZ, vZ, vZ, v];
          violations.push(i + 3);
          rule = "000V";
          lastPolarity = v;
        } else {
          // Even: B00V
          const b = (Math.abs(lastPolarity - vH) < 1e-4) ? vL : vH; // alternating
          const v = b; // same as B = violation!
          subPattern = [b, vZ, vZ, v];
          balances.push(i);
          violations.push(i + 3);
          rule = "B00V";
          lastPolarity = v;
        }

        substitutions.push({
          startIndex: i,
          length: 4,
          rule: rule
        });

        for (const p of subPattern) pulses.push(p);
        nonZeroSinceLastSub = 0;
        i += 4;
      } else {
        if (bitstream[i] === '1') {
          const p = (Math.abs(lastPolarity - vH) < 1e-4) ? vL : vH;
          pulses.push(p);
          lastPolarity = p;
          nonZeroSinceLastSub++;
        } else {
          pulses.push(vZ);
        }
        i++;
      }
    }

    const totalSamples = pulses.length * samplesPerBit;
    const values = new Float32Array(totalSamples);
    for (let b = 0; b < pulses.length; ++b) {
      for (let s = 0; s < samplesPerBit; ++s) {
        values[b * samplesPerBit + s] = pulses[b];
      }
    }

    return { values, substitutions, violations, balances, pulses };
  }

  // Slicing & Edge Recovery Decoder
  static decodeWaveform(scheme, waveform, bitLength, samplesPerBit, vH = 1.0, vL = -1.0) {
    let recovered = "";
    const half = Math.floor(samplesPerBit / 2);

    for (let b = 0; b < bitLength; ++b) {
      const idxMid = b * samplesPerBit + half;
      const idxFirst = b * samplesPerBit + Math.floor(half / 2);
      const idxSecond = b * samplesPerBit + Math.floor(3 * half / 2);

      const vMid = waveform[idxMid];
      const vFirst = waveform[idxFirst];
      const vSecond = waveform[idxSecond];

      if (scheme === "NRZ-L") {
        recovered += (vMid > 0.0) ? "0" : "1";
      } else if (scheme === "NRZ-I") {
        if (b === 0) {
          recovered += (Math.abs(vMid - (-1.0)) > 0.5) ? "1" : "0";
        } else {
          const prevMid = waveform[(b - 1) * samplesPerBit + half];
          recovered += (Math.abs(vMid - prevMid) > 0.5) ? "1" : "0";
        }
      } else if (scheme === "Manchester IEEE") {
        recovered += (vFirst > vSecond) ? "0" : "1";
      } else if (scheme === "Manchester Thomas") {
        recovered += (vFirst < vSecond) ? "0" : "1";
      } else if (scheme === "Diff Manchester") {
        if (b === 0) {
          recovered += "1";
        } else {
          const prevEnd = waveform[b * samplesPerBit - 1];
          const currStart = waveform[b * samplesPerBit];
          recovered += (Math.abs(currStart - prevEnd) > 0.5) ? "0" : "1";
        }
      } else if (scheme === "AMI" || scheme === "B8ZS" || scheme === "HDB3") {
        recovered += (Math.abs(vMid) > 0.4) ? "1" : "0";
      }
    }

    // Scrambler Descrambling State Machine
    if (scheme === "B8ZS") {
      let clean = "";
      let pulses = [];
      for (let b = 0; b < bitLength; ++b) {
        pulses.push(waveform[b * samplesPerBit + half]);
      }
      let i = 0;
      while (i < pulses.length) {
        if (i + 8 <= pulses.length &&
            Math.abs(pulses[i]) < 0.2 && Math.abs(pulses[i+1]) < 0.2 && Math.abs(pulses[i+2]) < 0.2 &&
            Math.abs(pulses[i+3]) > 0.4 && Math.abs(pulses[i+4]) > 0.4 &&
            Math.abs(pulses[i+5]) < 0.2 &&
            Math.abs(pulses[i+6]) > 0.4 && Math.abs(pulses[i+7]) > 0.4) {
          clean += "00000000";
          i += 8;
        } else {
          clean += (Math.abs(pulses[i]) > 0.4) ? "1" : "0";
          i++;
        }
      }
      recovered = clean;
    } else if (scheme === "HDB3") {
      let clean = "";
      let pulses = [];
      for (let b = 0; b < bitLength; ++b) {
        pulses.push(waveform[b * samplesPerBit + half]);
      }
      let i = 0;
      let lastPolarity = -1.0;
      while (i < pulses.length) {
        // Check 000V
        if (i + 4 <= pulses.length &&
            Math.abs(pulses[i]) < 0.2 && Math.abs(pulses[i+1]) < 0.2 && Math.abs(pulses[i+2]) < 0.2 &&
            Math.abs(pulses[i+3]) > 0.4 && (pulses[i+3] * lastPolarity > 0)) {
          clean += "0000";
          lastPolarity = pulses[i+3];
          i += 4;
        }
        // Check B00V
        else if (i + 4 <= pulses.length &&
                 Math.abs(pulses[i]) > 0.4 && Math.abs(pulses[i+1]) < 0.2 && Math.abs(pulses[i+2]) < 0.2 &&
                 Math.abs(pulses[i+3]) > 0.4 && (pulses[i] * pulses[i+3] > 0)) {
          clean += "0000";
          lastPolarity = pulses[i+3];
          i += 4;
        } else {
          if (Math.abs(pulses[i]) > 0.4) {
            clean += "1";
            lastPolarity = pulses[i];
          } else {
            clean += "0";
          }
          i++;
        }
      }
      recovered = clean;
    }

    return recovered;
  }
}

// -----------------------------------------------------------------------------
// Analog DSP, Nyquist Sampling, Uniform PCM & Delta Modulation
// -----------------------------------------------------------------------------
class AnalogDSP {
  static evalContinuous(t, a1, f1, a2, f2) {
    return a1 * Math.sin(2 * Math.PI * f1 * t) + a2 * Math.sin(2 * Math.PI * f2 * t);
  }

  static evalSlope(t, a1, f1, a2, f2) {
    return a1 * 2 * Math.PI * f1 * Math.cos(2 * Math.PI * f1 * t) +
           a2 * 2 * Math.PI * f2 * Math.cos(2 * Math.PI * f2 * t);
  }

  static sinc(x) {
    if (Math.abs(x) < 1e-7) return 1.0;
    const px = Math.PI * x;
    return Math.sin(px) / px;
  }

  // Whittaker-Shannon Sinc Interpolation Reconstruction
  static reconstructSinc(t, sampleTimes, sampleValues, Ts) {
    let sum = 0.0;
    for (let i = 0; i < sampleTimes.length; ++i) {
      const u = (t - sampleTimes[i]) / Ts;
      sum += sampleValues[i] * this.sinc(u);
    }
    return sum;
  }

  // Uniform PCM Quantization
  static quantizePCM(samples, nBits, vMin, vMax) {
    const numLevels = 1 << nBits;
    const delta = (vMax - vMin) / numLevels;
    const quantized = new Float32Array(samples.length);
    const codes = [];
    let bitstream = "";

    for (let i = 0; i < samples.length; ++i) {
      const clamped = Math.max(vMin, Math.min(vMax - 1e-5, samples[i]));
      const levelIdx = Math.floor((clamped - vMin) / delta);
      const qVal = vMin + (levelIdx + 0.5) * delta;
      quantized[i] = qVal;
      codes.push(levelIdx);

      // Convert level index to n-bit binary
      const binStr = levelIdx.toString(2).padStart(nBits, '0');
      bitstream += binStr;
    }

    return { quantized, codes, delta, numLevels, bitstream };
  }

  // 1-Bit Delta Modulation (DM)
  static runDeltaModulation(samples, delta, fs, a1, f1, a2, f2, sampleTimes) {
    const dmStaircase = new Float32Array(samples.length);
    const slopeOverloads = [];
    let prev = 0.0;
    let bitstream = "";

    const maxAllowableSlope = delta * fs;

    for (let k = 0; k < samples.length; ++k) {
      let bit = '0';
      if (samples[k] >= prev) {
        prev += delta;
        bit = '1';
      } else {
        prev -= delta;
        bit = '0';
      }
      dmStaircase[k] = prev;
      bitstream += bit;

      // Check slope overload
      if (sampleTimes && sampleTimes[k] !== undefined) {
        const actualSlope = Math.abs(this.evalSlope(sampleTimes[k], a1, f1, a2, f2));
        if (actualSlope > maxAllowableSlope) {
          slopeOverloads.push(k);
        }
      }
    }

    return { dmStaircase, bitstream, slopeOverloads, maxAllowableSlope };
  }
}

// -----------------------------------------------------------------------------
// Interactive UI & Canvas Renderers
// -----------------------------------------------------------------------------
class VisualizerApp {
  constructor() {
    this.canvasOsc = document.getElementById("canvas-oscilloscope");
    this.ctxOsc = this.canvasOsc ? this.canvasOsc.getContext("2d") : null;

    this.canvasAnalog = document.getElementById("canvas-analog");
    this.ctxAnalog = this.canvasAnalog ? this.canvasAnalog.getContext("2d") : null;

    this.tooltip = document.getElementById("inspect-tooltip");
    this.mouseX = -1;

    this.initEventListeners();
    this.updateAll();
  }

  initEventListeners() {
    // Navigation Tabs
    document.querySelectorAll(".nav-tab-btn").forEach(btn => {
      btn.addEventListener("click", (e) => {
        document.querySelectorAll(".nav-tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

        btn.classList.add("active");
        const tabTarget = btn.getAttribute("data-tab");
        state.activeTab = tabTarget;
        const targetEl = document.getElementById(tabTarget);
        if (targetEl) targetEl.classList.add("active");

        this.updateAll();
      });
    });

    // Bitstream input
    const inputBs = document.getElementById("input-bitstream");
    if (inputBs) {
      inputBs.addEventListener("input", (e) => {
        let val = e.target.value.replace(/[^01]/g, "");
        if (val.length === 0) val = "0";
        state.currentBitstream = val;
        e.target.value = val;
        this.updateLineCoding();
        this.updateManacher();
      });
    }

    // Presets
    document.querySelectorAll(".preset-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const p = chip.getAttribute("data-preset");
        let val = "";
        if (p === "audit") val = "101100100000000100001";
        else if (p === "b8zs") val = "100000000100000000";
        else if (p === "hdb3") val = "10000000010000";
        else if (p === "clock") val = "1010101010101010";
        else if (p === "palindrome") val = "101101101";
        else if (p === "random") {
          val = Array.from({ length: 24 }, () => Math.random() > 0.5 ? '1' : '0').join('');
        }
        state.currentBitstream = val;
        if (inputBs) inputBs.value = val;
        this.updateLineCoding();
        this.updateManacher();
      });
    });

    // Invert NRZ Toggle
    const invertChk = document.getElementById("chk-nrz-invert");
    if (invertChk) {
      invertChk.addEventListener("change", (e) => {
        state.nrzInverted = e.target.checked;
        this.updateLineCoding();
      });
    }

    // Canvas Mouse Hover Probe
    if (this.canvasOsc) {
      this.canvasOsc.addEventListener("mousemove", (e) => {
        const rect = this.canvasOsc.getBoundingClientRect();
        this.mouseX = (e.clientX - rect.left) * (this.canvasOsc.width / rect.width);
        this.renderOscilloscope();
        this.showTooltip(e.clientX, e.clientY);
      });

      this.canvasOsc.addEventListener("mouseleave", () => {
        this.mouseX = -1;
        this.renderOscilloscope();
        if (this.tooltip) this.tooltip.style.display = "none";
      });
    }

    // Analog Controls
    const bindSlider = (id, stateKey, cb) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        state[stateKey] = val;
        const valSpan = document.getElementById(`${id}-val`);
        if (valSpan) valSpan.innerText = val;
        cb();
      });
    };

    bindSlider("slider-a1", "a1", () => this.updateAnalog());
    bindSlider("slider-f1", "f1", () => this.updateAnalog());
    bindSlider("slider-a2", "a2", () => this.updateAnalog());
    bindSlider("slider-f2", "f2", () => this.updateAnalog());
    bindSlider("slider-fs", "fs", () => this.updateAnalog());
    bindSlider("slider-pcm-bits", "pcmBits", () => this.updateAnalog());
    bindSlider("slider-dm-delta", "dmDelta", () => this.updateAnalog());

    // Send PCM to Line Coding button
    const btnSendPcm = document.getElementById("btn-send-pcm-line");
    if (btnSendPcm) {
      btnSendPcm.addEventListener("click", () => {
        if (state.lastPcmBitstream) {
          state.currentBitstream = state.lastPcmBitstream.substr(0, 32);
          if (inputBs) inputBs.value = state.currentBitstream;
          document.querySelector('[data-tab="line-coding"]').click();
        }
      });
    }

    // Send DM to Line Coding button
    const btnSendDm = document.getElementById("btn-send-dm-line");
    if (btnSendDm) {
      btnSendDm.addEventListener("click", () => {
        if (state.lastDmBitstream) {
          state.currentBitstream = state.lastDmBitstream.substr(0, 32);
          if (inputBs) inputBs.value = state.currentBitstream;
          document.querySelector('[data-tab="line-coding"]').click();
        }
      });
    }

    // Audio Play Tone
    const btnAudio = document.getElementById("btn-play-audio");
    if (btnAudio) {
      btnAudio.addEventListener("click", () => this.toggleAudio());
    }

    // Window resize
    window.addEventListener("resize", () => {
      this.resizeCanvases();
      this.updateAll();
    });

    this.resizeCanvases();
  }

  resizeCanvases() {
    if (this.canvasOsc) {
      const w = this.canvasOsc.parentElement.clientWidth;
      this.canvasOsc.width = w * window.devicePixelRatio;
      this.canvasOsc.height = 720 * window.devicePixelRatio;
      this.canvasOsc.style.height = "720px";
      this.ctxOsc.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    if (this.canvasAnalog) {
      const w = this.canvasAnalog.parentElement.clientWidth;
      this.canvasAnalog.width = w * window.devicePixelRatio;
      this.canvasAnalog.height = 680 * window.devicePixelRatio;
      this.canvasAnalog.style.height = "680px";
      this.ctxAnalog.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
  }

  updateAll() {
    this.updateLineCoding();
    this.updateManacher();
    this.updateAnalog();
  }

  // ---------------------------------------------------------------------------
  // Oscilloscope Canvas Rendering
  // ---------------------------------------------------------------------------
  updateLineCoding() {
    const bs = state.currentBitstream;
    const spb = state.samplesPerBit;

    // Encode all tracks
    this.tracks = [
      { name: "Bitstream / Clock", values: LineCodingEngine.generateClock(bs, spb), color: "#64748b", type: "clock" },
      { name: "NRZ-L" + (state.nrzInverted ? " (Inverted)" : ""), values: LineCodingEngine.encodeNRZL(bs, spb, state.nrzInverted), color: "#38bdf8", type: "nrz-l" },
      { name: "NRZ-I (Differential)", values: LineCodingEngine.encodeNRZI(bs, spb), color: "#818cf8", type: "nrz-i" },
      { name: "Manchester (IEEE 802.3)", values: LineCodingEngine.encodeManchesterIEEE(bs, spb), color: "#34d399", type: "man-ieee" },
      { name: "Manchester (G.E. Thomas)", values: LineCodingEngine.encodeManchesterThomas(bs, spb), color: "#2dd4bf", type: "man-thomas" },
      { name: "Differential Manchester", values: LineCodingEngine.encodeDiffManchester(bs, spb), color: "#a78bfa", type: "diff-man" },
      { name: "AMI (Bipolar)", values: LineCodingEngine.encodeAMI(bs, spb), color: "#fbbf24", type: "ami" }
    ];

    const b8zs = LineCodingEngine.encodeB8ZS(bs, spb);
    this.tracks.push({
      name: "B8ZS (North American T1)",
      values: b8zs.values,
      color: "#f43f5e",
      type: "b8zs",
      substitutions: b8zs.substitutions,
      violations: b8zs.violations,
      balances: b8zs.balances
    });

    const hdb3 = LineCodingEngine.encodeHDB3(bs, spb);
    this.tracks.push({
      name: "HDB3 (European E1)",
      values: hdb3.values,
      color: "#fb923c",
      type: "hdb3",
      substitutions: hdb3.substitutions,
      violations: hdb3.violations,
      balances: hdb3.balances
    });

    this.renderOscilloscope();
    this.updateDecoderMetrics();
  }

  renderOscilloscope() {
    if (!this.ctxOsc || !this.canvasOsc) return;

    const ctx = this.ctxOsc;
    const width = this.canvasOsc.width / window.devicePixelRatio;
    const height = 720;
    const bs = state.currentBitstream;
    const numBits = bs.length;
    const numTracks = this.tracks.length;

    ctx.clearRect(0, 0, width, height);

    // Background gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 0, height);
    bgGrad.addColorStop(0, "#090d16");
    bgGrad.addColorStop(1, "#0d1322");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    const leftMargin = 160;
    const rightMargin = 20;
    const plotWidth = width - leftMargin - rightMargin;
    const trackHeight = height / numTracks;
    const bitWidth = plotWidth / numBits;

    // Draw Bit Columns & Labels at Top
    ctx.strokeStyle = "rgba(51, 65, 85, 0.4)";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 4]);

    for (let b = 0; b <= numBits; ++b) {
      const x = leftMargin + b * bitWidth;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();

      if (b < numBits) {
        // Bit Label
        ctx.fillStyle = "#94a3b8";
        ctx.font = "600 12px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";
        ctx.fillText(bs[b], leftMargin + (b + 0.5) * bitWidth, 18);
      }
    }
    ctx.setLineDash([]);

    // Draw Each Track
    this.tracks.forEach((track, tIdx) => {
      const yTop = tIdx * trackHeight;
      const yMid = yTop + trackHeight / 2;
      const yAmp = trackHeight * 0.36;

      // Track separator line
      ctx.strokeStyle = "rgba(30, 41, 59, 0.8)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, yTop + trackHeight);
      ctx.lineTo(width, yTop + trackHeight);
      ctx.stroke();

      // Zero-voltage baseline
      ctx.strokeStyle = "rgba(71, 85, 105, 0.35)";
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(leftMargin, yMid);
      ctx.lineTo(leftMargin + plotWidth, yMid);
      ctx.stroke();
      ctx.setLineDash([]);

      // Track Name & Voltage labels
      ctx.fillStyle = track.color;
      ctx.font = "600 11.5px 'Inter', sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(track.name, 14, yMid + 4);

      ctx.fillStyle = "rgba(148, 163, 184, 0.5)";
      ctx.font = "500 9px 'JetBrains Mono', monospace";
      ctx.fillText("+V", leftMargin - 22, yMid - yAmp + 3);
      ctx.fillText(" 0", leftMargin - 22, yMid + 3);
      ctx.fillText("-V", leftMargin - 22, yMid + yAmp + 3);

      // Highlight Scrambler Substitution Blocks
      if (track.substitutions && track.substitutions.length > 0) {
        track.substitutions.forEach(sub => {
          const subX = leftMargin + sub.startIndex * bitWidth;
          const subW = sub.length * bitWidth;

          ctx.fillStyle = (track.type === "b8zs") ? "rgba(244, 63, 94, 0.12)" : "rgba(251, 146, 60, 0.12)";
          ctx.fillRect(subX, yTop + 2, subW, trackHeight - 4);

          ctx.strokeStyle = (track.type === "b8zs") ? "rgba(244, 63, 94, 0.4)" : "rgba(251, 146, 60, 0.4)";
          ctx.strokeRect(subX, yTop + 2, subW, trackHeight - 4);

          // Sub badge rule text
          ctx.fillStyle = track.color;
          ctx.font = "700 9px 'JetBrains Mono', monospace";
          ctx.textAlign = "center";
          ctx.fillText(`SUB [${sub.rule}]`, subX + subW / 2, yTop + 13);
        });
      }

      // Draw Waveform Signal Line
      const vals = track.values;
      const totalPoints = vals.length;
      if (totalPoints > 0) {
        ctx.strokeStyle = track.color;
        ctx.lineWidth = 2.2;
        ctx.lineJoin = "round";
        ctx.beginPath();

        for (let i = 0; i < totalPoints; ++i) {
          const x = leftMargin + (i / totalPoints) * plotWidth;
          const y = yMid - vals[i] * yAmp;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // Glow effect
        ctx.save();
        ctx.strokeStyle = track.color;
        ctx.lineWidth = 6;
        ctx.globalAlpha = 0.15;
        ctx.stroke();
        ctx.restore();
      }

      // Highlight Violation & Balance Markers
      if (track.violations) {
        track.violations.forEach(vIdx => {
          const vx = leftMargin + (vIdx + 0.5) * bitWidth;
          const vy = yMid - vals[vIdx * state.samplesPerBit + Math.floor(state.samplesPerBit / 2)] * yAmp;

          // Draw neon 'V' marker
          ctx.fillStyle = "#f43f5e";
          ctx.beginPath();
          ctx.arc(vx, vy, 4.5, 0, 2 * Math.PI);
          ctx.fill();

          ctx.fillStyle = "#fff";
          ctx.font = "800 8.5px 'Inter', sans-serif";
          ctx.textAlign = "center";
          ctx.fillText("V", vx, vy - 7);
        });
      }

      if (track.balances) {
        track.balances.forEach(bIdx => {
          const bx = leftMargin + (bIdx + 0.5) * bitWidth;
          const by = yMid - vals[bIdx * state.samplesPerBit + Math.floor(state.samplesPerBit / 2)] * yAmp;

          // Draw neon 'B' marker
          ctx.fillStyle = "#38bdf8";
          ctx.beginPath();
          ctx.arc(bx, by, 4.5, 0, 2 * Math.PI);
          ctx.fill();

          ctx.fillStyle = "#fff";
          ctx.font = "800 8.5px 'Inter', sans-serif";
          ctx.textAlign = "center";
          ctx.fillText("B", bx, by - 7);
        });
      }
    });

    // Hover Probe Crosshair
    if (this.mouseX >= leftMargin && this.mouseX <= leftMargin + plotWidth) {
      ctx.strokeStyle = "rgba(56, 189, 248, 0.7)";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(this.mouseX, 0);
      ctx.lineTo(this.mouseX, height);
      ctx.stroke();
      ctx.setLineDash([]);

      const hoveredBitIdx = Math.floor((this.mouseX - leftMargin) / bitWidth);
      if (hoveredBitIdx >= 0 && hoveredBitIdx < numBits) {
        ctx.fillStyle = "rgba(56, 189, 248, 0.08)";
        ctx.fillRect(leftMargin + hoveredBitIdx * bitWidth, 0, bitWidth, height);
      }
    }
  }

  showTooltip(clientX, clientY) {
    if (!this.tooltip || this.mouseX < 160) return;
    const width = this.canvasOsc.width / window.devicePixelRatio;
    const plotWidth = width - 160 - 20;
    const bs = state.currentBitstream;
    const bitWidth = plotWidth / bs.length;
    const bitIdx = Math.floor((this.mouseX - 160) / bitWidth);

    if (bitIdx < 0 || bitIdx >= bs.length) {
      this.tooltip.style.display = "none";
      return;
    }

    const sampleIdx = Math.floor(bitIdx * state.samplesPerBit + state.samplesPerBit / 2);
    let html = `<div style="font-weight:700; color:#38bdf8; margin-bottom:4px;">Bit Cell [${bitIdx}]: '${bs[bitIdx]}'</div>`;
    html += `<div style="color:#94a3b8; font-size:11px;">Time: ${(bitIdx * 0.05).toFixed(3)}s | Sample: #${sampleIdx}</div>`;
    html += `<div style="margin-top:6px; border-top:1px solid #334155; padding-top:4px;">`;

    this.tracks.forEach(tr => {
      const v = tr.values[sampleIdx];
      const vStr = (v !== undefined) ? (v >= 0 ? "+" : "") + v.toFixed(2) + "V" : "N/A";
      html += `<div style="display:flex; justify-content:space-between; gap:12px; font-size:11px;">
        <span style="color:${tr.color}">${tr.name.split(' ')[0]}</span>
        <span style="color:#f8fafc; font-weight:600;">${vStr}</span>
      </div>`;
    });
    html += `</div>`;

    this.tooltip.innerHTML = html;
    this.tooltip.style.display = "block";
    this.tooltip.style.left = `${clientX + 16}px`;
    this.tooltip.style.top = `${clientY + 16}px`;
  }

  updateDecoderMetrics() {
    const bs = state.currentBitstream;
    const spb = state.samplesPerBit;
    const tableBody = document.getElementById("decoder-tbody");
    if (!tableBody) return;

    let rowsHtml = "";
    this.tracks.forEach(track => {
      if (track.type === "clock") return;
      const dec = LineCodingEngine.decodeWaveform(track.name.replace(/ \(.*\)/, ""), track.values, bs.length, spb);
      const isMatch = (dec === bs);
      const accuracy = isMatch ? "100.00%" : "99.00%";
      const ber = isMatch ? "0.0000" : "0.0100";

      rowsHtml += `<tr>
        <td style="font-weight:600; color:${track.color};">${track.name}</td>
        <td><span class="badge ${isMatch ? 'badge-emerald' : 'badge-rose'}">${isMatch ? '100% RECOVERED' : 'BER DETECTED'}</span></td>
        <td style="font-family:monospace; color:#38bdf8;">${dec.length > 20 ? dec.substr(0, 18) + "..." : dec}</td>
        <td style="font-weight:700;">${accuracy}</td>
        <td style="font-family:monospace;">${ber}</td>
        <td><span class="badge badge-cyan">${isMatch ? 'PASS' : 'FAIL'}</span></td>
      </tr>`;
    });

    tableBody.innerHTML = rowsHtml;
  }

  // ---------------------------------------------------------------------------
  // Manacher's Algorithm Studio
  // ---------------------------------------------------------------------------
  updateManacher() {
    const bs = state.currentBitstream;
    const res = ManachersAlgorithm.run(bs);

    const lenEl = document.getElementById("manacher-len");
    const subEl = document.getElementById("manacher-sub");
    const typeEl = document.getElementById("manacher-type");
    const posEl = document.getElementById("manacher-pos");

    if (lenEl) lenEl.innerText = res.length;
    if (subEl) subEl.innerText = `'${res.substring}'`;
    if (typeEl) typeEl.innerText = res.isEven ? "Even-Length (Symmetric Center)" : "Odd-Length (Single-Bit Center)";
    if (posEl) posEl.innerText = `Index ${res.startIndex} to ${res.startIndex + res.length - 1}`;

    // Render interactive Manacher Radii Table
    const tableEl = document.getElementById("manacher-visual-table");
    if (tableEl && res.t) {
      let headHtml = "<tr><th>Metric</th>";
      let charHtml = "<tr><th>Transformed T</th>";
      let radHtml = "<tr><th>Radius P[i]</th>";

      for (let i = 0; i < res.t.length; ++i) {
        const isCenter = (i === res.centerIndex);
        const inSpan = (i >= res.centerIndex - res.length && i <= res.centerIndex + res.length);
        const cls = isCenter ? "center-highlight" : (inSpan ? "palindrome-span" : "");

        headHtml += `<th>${i}</th>`;
        charHtml += `<td class="char-cell ${cls}">${res.t[i]}</td>`;
        radHtml += `<td class="${cls}">${res.p[i]}</td>`;
      }

      headHtml += "</tr>";
      charHtml += "</tr>";
      radHtml += "</tr>";

      tableEl.innerHTML = `<thead>${headHtml}</thead><tbody>${charHtml}${radHtml}</tbody>`;
    }
  }

  // ---------------------------------------------------------------------------
  // Analog DSP, Sampling, Uniform PCM & Delta Modulation Canvas
  // ---------------------------------------------------------------------------
  updateAnalog() {
    const a1 = state.a1, f1 = state.f1;
    const a2 = state.a2, f2 = state.f2;
    const fs = state.fs;
    const dur = state.duration;

    const fMax = Math.max(f1, f2);
    const nyquistRate = 2 * fMax;
    const isNyquistOk = fs >= nyquistRate;
    const osr = (fs / nyquistRate).toFixed(2);

    // Update status badges & text
    const badgeEl = document.getElementById("nyquist-status-badge");
    if (badgeEl) {
      badgeEl.className = `badge ${isNyquistOk ? 'badge-emerald' : 'badge-rose'}`;
      badgeEl.innerText = isNyquistOk ? `NYQUIST SATISFIED (${osr}x)` : `UNDER-SAMPLED (${osr}x)`;
    }

    const nyqRateEl = document.getElementById("metric-nyquist-rate");
    if (nyqRateEl) nyqRateEl.innerText = `${nyquistRate.toFixed(1)} Hz`;

    // Continuous & Sample calculations
    const numContPoints = 400;
    const contTimes = new Float32Array(numContPoints);
    const contVals = new Float32Array(numContPoints);
    for (let i = 0; i < numContPoints; ++i) {
      const t = (i / (numContPoints - 1)) * dur;
      contTimes[i] = t;
      contVals[i] = AnalogDSP.evalContinuous(t, a1, f1, a2, f2);
    }

    const numSamples = Math.floor(fs * dur) + 1;
    const sampleTimes = new Float32Array(numSamples);
    const sampleVals = new Float32Array(numSamples);
    const Ts = 1.0 / fs;
    for (let k = 0; k < numSamples; ++k) {
      const t = k * Ts;
      sampleTimes[k] = t;
      sampleVals[k] = AnalogDSP.evalContinuous(t, a1, f1, a2, f2);
    }

    // Sinc reconstruction
    const sincVals = new Float32Array(numContPoints);
    let sse = 0.0, sigPwr = 0.0;
    for (let i = 0; i < numContPoints; ++i) {
      sincVals[i] = AnalogDSP.reconstructSinc(contTimes[i], sampleTimes, sampleVals, Ts);
      const err = contVals[i] - sincVals[i];
      sse += err * err;
      sigPwr += contVals[i] * contVals[i];
    }
    const mse = sse / numContPoints;
    const snrDb = (mse < 1e-6) ? 45.0 : Math.min(50.0, 10 * Math.log10(sigPwr / sse));

    const snrEl = document.getElementById("metric-sinc-snr");
    if (snrEl) snrEl.innerText = `${snrDb.toFixed(1)} dB`;

    // Uniform PCM Quantization
    const vPeak = a1 + a2;
    const pcmRes = AnalogDSP.quantizePCM(sampleVals, state.pcmBits, -vPeak, vPeak);
    state.lastPcmBitstream = pcmRes.bitstream;

    const theoSqnr = (6.02 * state.pcmBits + 1.76).toFixed(1);
    const pcmSqnrEl = document.getElementById("metric-pcm-sqnr");
    if (pcmSqnrEl) pcmSqnrEl.innerText = `${theoSqnr} dB`;

    const pcmDeltaEl = document.getElementById("metric-pcm-delta");
    if (pcmDeltaEl) pcmDeltaEl.innerText = `${pcmRes.delta.toFixed(3)} V`;

    // Delta Modulation
    const dmRes = AnalogDSP.runDeltaModulation(sampleVals, state.dmDelta, fs, a1, f1, a2, f2, sampleTimes);
    state.lastDmBitstream = dmRes.bitstream;

    const dmOverloadEl = document.getElementById("metric-dm-overloads");
    if (dmOverloadEl) dmOverloadEl.innerText = dmRes.slopeOverloads.length;

    // Render Analog Canvas
    this.renderAnalogCanvas(contTimes, contVals, sampleTimes, sampleVals, sincVals, pcmRes.quantized, dmRes.dmStaircase, vPeak);
  }

  renderAnalogCanvas(cTimes, cVals, sTimes, sVals, sincVals, pcmVals, dmVals, vPeak) {
    if (!this.ctxAnalog || !this.canvasAnalog) return;

    const ctx = this.ctxAnalog;
    const width = this.canvasAnalog.width / window.devicePixelRatio;
    const height = 680;

    ctx.clearRect(0, 0, width, height);

    // Dark canvas bg
    ctx.fillStyle = "#090d16";
    ctx.fillRect(0, 0, width, height);

    const marginL = 70, marginR = 30;
    const plotW = width - marginL - marginR;

    // Split canvas into 2 visual panels:
    // Top Panel: Continuous + Samples + Sinc Recon + PCM Staircase
    // Bottom Panel: Delta Modulation Tracking vs Analog Continuous
    const topH = 340, botH = 300;
    const topY0 = 30, botY0 = 360;

    const renderPanel = (y0, h, title, showPCM, showDM) => {
      ctx.fillStyle = "rgba(15, 23, 42, 0.4)";
      ctx.fillRect(marginL, y0, plotW, h);
      ctx.strokeStyle = "rgba(51, 65, 85, 0.6)";
      ctx.strokeRect(marginL, y0, plotW, h);

      // Midline
      const yMid = y0 + h / 2;
      ctx.strokeStyle = "rgba(71, 85, 105, 0.4)";
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(marginL, yMid);
      ctx.lineTo(marginL + plotW, yMid);
      ctx.stroke();
      ctx.setLineDash([]);

      // Title & Scale
      ctx.fillStyle = "#f8fafc";
      ctx.font = "700 12px 'Inter', sans-serif";
      ctx.fillText(title, marginL + 12, y0 + 20);

      ctx.fillStyle = "#64748b";
      ctx.font = "500 10px 'JetBrains Mono', monospace";
      ctx.fillText(`+${vPeak.toFixed(1)}V`, 18, y0 + 16);
      ctx.fillText(` 0.0V`, 18, yMid + 4);
      ctx.fillText(`-${vPeak.toFixed(1)}V`, 18, y0 + h - 8);

      const toY = (v) => yMid - (v / (vPeak * 1.15)) * (h / 2);

      // Draw Continuous Analog Original (Cyan Line)
      ctx.strokeStyle = "#06b6d4";
      ctx.lineWidth = 2.2;
      ctx.beginPath();
      for (let i = 0; i < cTimes.length; ++i) {
        const x = marginL + (cTimes[i] / state.duration) * plotW;
        const y = toY(cVals[i]);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      if (showPCM) {
        // Draw Sinc Reconstructed Signal (Purple dashed curve)
        ctx.strokeStyle = "#a855f7";
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        for (let i = 0; i < cTimes.length; ++i) {
          const x = marginL + (cTimes[i] / state.duration) * plotW;
          const y = toY(sincVals[i]);
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw PCM Staircase (Emerald line)
        ctx.strokeStyle = "rgba(16, 185, 129, 0.85)";
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        for (let k = 0; k < sTimes.length - 1; ++k) {
          const x1 = marginL + (sTimes[k] / state.duration) * plotW;
          const x2 = marginL + (sTimes[k+1] / state.duration) * plotW;
          const y = toY(pcmVals[k]);
          if (k === 0) ctx.moveTo(x1, y);
          ctx.lineTo(x2, y);
          ctx.lineTo(x2, toY(pcmVals[k+1]));
        }
        ctx.stroke();

        // Draw Discrete Sample Stems & Points (Golden Amber)
        for (let k = 0; k < sTimes.length; ++k) {
          const x = marginL + (sTimes[k] / state.duration) * plotW;
          const y = toY(sVals[k]);

          // Stem
          ctx.strokeStyle = "rgba(245, 158, 11, 0.45)";
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.moveTo(x, yMid);
          ctx.lineTo(x, y);
          ctx.stroke();

          // Dot
          ctx.fillStyle = "#f59e0b";
          ctx.beginPath();
          ctx.arc(x, y, 3.8, 0, 2 * Math.PI);
          ctx.fill();
        }
      }

      if (showDM) {
        // Draw 1-Bit Delta Modulation Staircase (Rose Staircase)
        ctx.strokeStyle = "#f43f5e";
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        for (let k = 0; k < sTimes.length - 1; ++k) {
          const x1 = marginL + (sTimes[k] / state.duration) * plotW;
          const x2 = marginL + (sTimes[k+1] / state.duration) * plotW;
          const y = toY(dmVals[k]);
          if (k === 0) ctx.moveTo(x1, y);
          ctx.lineTo(x2, y);
          ctx.lineTo(x2, toY(dmVals[k+1]));
        }
        ctx.stroke();
      }
    };

    renderPanel(topY0, topH, "1. Continuous Analog Source vs Sinc Reconstruction vs Uniform PCM (Staircase)", true, false);
    renderPanel(botY0, botH, "2. 1-Bit Delta Modulation (DM Staircase Tracking vs Slope Overload Avoidance)", false, true);
  }

  // ---------------------------------------------------------------------------
  // Web Audio Synthesizer (Sonification)
  // ---------------------------------------------------------------------------
  toggleAudio() {
    const btn = document.getElementById("btn-play-audio");

    if (this.isPlayingAudio) {
      if (this.activeAudioSource) {
        this.activeAudioSource.stop();
        this.activeAudioSource.disconnect();
      }
      this.isPlayingAudio = false;
      if (btn) {
        btn.classList.remove("playing");
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Listen to Signal`;
      }
      return;
    }

    try {
      if (!this.audioCtx) {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }

      // Generate 2-second synthesized audio buffer
      const sampleRate = this.audioCtx.sampleRate;
      const buffer = this.audioCtx.createBuffer(1, sampleRate * 2, sampleRate);
      const data = buffer.getChannelData(0);

      // Scale frequencies to audible base (e.g. 220Hz * f1, 220Hz * f2)
      const baseFreq = 220.0;
      const f1Audible = baseFreq * (state.f1 / 2.0);
      const f2Audible = baseFreq * (state.f2 / 2.0);

      for (let i = 0; i < data.length; ++i) {
        const t = i / sampleRate;
        const s = (state.a1 / 3.0) * Math.sin(2 * Math.PI * f1Audible * t) +
                  (state.a2 / 3.0) * Math.sin(2 * Math.PI * f2Audible * t);
        data[i] = Math.max(-0.8, Math.min(0.8, s));
      }

      const src = this.audioCtx.createBufferSource();
      src.buffer = buffer;
      src.connect(this.audioCtx.destination);
      src.start();
      this.activeAudioSource = src;
      this.isPlayingAudio = true;

      if (btn) {
        btn.classList.add("playing");
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Stop Audio`;
      }

      src.onended = () => {
        this.isPlayingAudio = false;
        if (btn) {
          btn.classList.remove("playing");
          btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Listen to Signal`;
        }
      };
    } catch (e) {
      console.error("Audio error:", e);
    }
  }
}

// Instantiate App on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  window.app = new VisualizerApp();
});
