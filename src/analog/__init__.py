"""Analog signal processing package for ITT 036 Assignment."""
from .continuous_signal import ContinuousSignal, ToneComponent
from .sampling import NyquistSampler, SamplingResult
from .plotter import plot_continuous_and_sampled, plot_nyquist_reconstruction

__all__ = [
    "ContinuousSignal",
    "ToneComponent",
    "NyquistSampler",
    "SamplingResult",
    "plot_continuous_and_sampled",
    "plot_nyquist_reconstruction",
]


