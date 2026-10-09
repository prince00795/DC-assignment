"""
Analog Signal Visualization Utility
===================================
Provides plotting tools for continuous waveforms, Nyquist sampling points,
and multi-tone frequency components using Matplotlib.
"""

from __future__ import annotations
from typing import Optional, Tuple
from src.analog.continuous_signal import ContinuousSignal


def plot_continuous_and_sampled(
    signal: ContinuousSignal,
    sampling_rate: float,
    duration: float,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Optional[object]:
    """
    Plots the continuous analog signal x(t) alongside discrete Nyquist sampling points.

    :param signal: ContinuousSignal instance to plot.
    :param sampling_rate: Sampling frequency fs (Hz).
    :param duration: Total duration to display (seconds).
    :param title: Plot title.
    :param save_path: Optional file path to save the generated image (.png, .svg).
    :return: Matplotlib figure object if matplotlib is installed, otherwise None.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend safe for headless/server use
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    # Continuous high-resolution reference wave
    t_cont, v_cont = signal.generate_continuous_waveform(duration=duration, points_per_cycle=100)
    # Discrete sampled points
    t_samp, v_samp = signal.sample(sampling_rate=sampling_rate, duration=duration)

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=100)
    ax.plot(t_cont, v_cont, label="Continuous x(t)", color="#1f77b4", linewidth=1.8, alpha=0.9)
    ax.stem(
        t_samp,
        v_samp,
        linefmt="r--",
        markerfmt="ro",
        basefmt="k-",
        label=f"Sampled Points (fs={sampling_rate:.1f} Hz)",
    )

    is_nyquist = signal.is_nyquist_satisfied(sampling_rate)
    status_text = "Nyquist Satisfied (No Aliasing)" if is_nyquist else "Under-sampled (Aliasing Risk!)"
    color_status = "green" if is_nyquist else "red"

    ax.set_title(
        title or f"Analog Signal Sampling: {signal.summary().splitlines()[0]}",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Time t (seconds)")
    ax.set_ylabel("Amplitude x(t) (Volts)")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper right")
    ax.text(
        0.02,
        0.95,
        f"Nyquist Rate: {signal.nyquist_rate:.1f} Hz | {status_text}",
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=color_status, alpha=0.8),
    )

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
        return None

    return fig


def plot_nyquist_reconstruction(
    signal: ContinuousSignal,
    sampling_result: object,
    duration: Optional[float] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Optional[object]:
    """
    Plots the original analog signal, discrete samples, and Whittaker-Shannon sinc reconstruction.

    :param signal: Original ContinuousSignal instance.
    :param sampling_result: SamplingResult instance from NyquistSampler.
    :param duration: Time window to evaluate (defaults to sampling_result.duration).
    :param title: Custom plot title.
    :param save_path: Optional path to save image file.
    :return: Matplotlib figure object if available.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None

    dur = duration if duration is not None else getattr(sampling_result, "duration", 1.0)
    t_cont, v_cont = signal.generate_continuous_waveform(duration=dur, points_per_cycle=100)

    # Reconstruct continuous wave via sinc interpolation
    eval_times = list(t_cont)
    reconstructed = sampling_result.reconstruct_sinc(eval_times)

    metrics = sampling_result.compute_reconstruction_metrics(signal)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, dpi=100)

    # Upper panel: Original vs Reconstructed
    ax1.plot(t_cont, v_cont, label="Original x(t)", color="#1f77b4", linewidth=2.0)
    ax1.plot(eval_times, reconstructed, "--", label="Whittaker-Shannon Sinc Recon x_hat(t)", color="#2ca02c", linewidth=1.8)

    sample_times = getattr(sampling_result, "sample_times", [])
    sample_values = getattr(sampling_result, "sample_values", [])
    fs = getattr(sampling_result, "sampling_rate", 1.0)
    ax1.stem(sample_times, sample_values, linefmt="r:", markerfmt="ro", basefmt="k-", label=f"Samples (fs={fs:.1f}Hz)")

    is_satisfied = getattr(sampling_result, "is_nyquist_satisfied", False)
    status_str = "Nyquist Satisfied (fs >= 2*f_max)" if is_satisfied else "Aliased (fs < 2*f_max)"
    badge_color = "green" if is_satisfied else "red"

    ax1.set_title(title or f"Nyquist Reconstruction Analysis: {status_str}", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Amplitude (V)")
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper right", fontsize=8)
    ax1.text(
        0.02,
        0.95,
        f"MSE: {metrics['mse']:.4e} | SNR: {metrics['snr_db']:.1f} dB",
        transform=ax1.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=badge_color, alpha=0.8),
    )

    # Lower panel: Reconstruction Error
    errors = [r - y for r, y in zip(reconstructed, v_cont)]
    ax2.plot(eval_times, errors, color="#d62728", linewidth=1.5, label="Reconstruction Error: e(t) = x_hat(t) - x(t)")
    ax2.axhline(0, color="black", linestyle="--", linewidth=0.8, alpha=0.7)
    ax2.set_xlabel("Time t (seconds)")
    ax2.set_ylabel("Error (V)")
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="upper right", fontsize=8)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150)
        plt.close(fig)
        return None

    return fig

