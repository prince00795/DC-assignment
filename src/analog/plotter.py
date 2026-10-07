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
