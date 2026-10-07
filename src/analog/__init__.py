"""Analog signal processing package for ITT 036 Assignment."""
from .continuous_signal import ContinuousSignal, ToneComponent
from .plotter import plot_continuous_and_sampled

__all__ = ["ContinuousSignal", "ToneComponent", "plot_continuous_and_sampled"]
