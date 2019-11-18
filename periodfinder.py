#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 17:38:51 2019

@author: alexis
"""
import numpy as np
import collections
from filters import bandpass_and_integrate


def _root(x1, x2, y1, y2):
    """x position of the root of the affine function going through (x1,y1) and (x2,y2)."""
    return x1 - y1 * (x2-x1) / (y2-y1)

class PeriodFinder:
    def __init__(self, fs=44100, filt=None,
                 n_periods=2):
        """
        Parameters
        ----------
        fs : sampling frequency
        filt : Filter to apply to data
        n_periods : number of periods over which to average
        """
        self._fs = fs
        if filt==None:
            filt = bandpass_and_integrate()
        self._filter = filt
        self._n_periods = n_periods
        self._last_periods = collections.deque([], n_periods) # in samples
        self._samples_seen = 0 # samples since beginning
        self._last_value = 0.0 # value of filtered data at last analyzed sample
        self._last_period_beginning = 0.0 # in samples

    def __call__(self, indata):
        """Returns the estimated frequency of the signal."""
        self.analyze(indata)
        return self.get_estimated_frequency()

    def analyze(self, indata):
        filtered = self._filter(indata)
        sign_changes = np.diff((filtered > 0)*1, prepend=self._last_value > 0)
        rising, = np.where(sign_changes == 1)
#        print(filtered)
#        print(rising)
#        print(filtered[rising-1])
#        print(filtered[rising])
        for i in rising:
            if i == 0:
                # Record rising zero
                assert self._last_value <= 0 and filtered[0] > 0
                self._record_rising_zero(_root(-1, 0, self._last_value, filtered[0]))
            else:
                assert filtered[i-1] <= 0 and filtered[i] > 0
                self._record_rising_zero(_root(i-1, i, filtered[i-1], filtered[i]))

        self._last_value = filtered[-1]
        self._samples_seen += len(indata)

    def _record_rising_zero(self, samples_local):
        samples_abs = samples_local + self._samples_seen
        # Deque erases data automatically if needed
        self._last_periods.append(samples_abs - self._last_period_beginning)
        self._last_period_beginning = samples_abs

    def get_estimated_period(self):
        """Estimated period in samples."""
        if len(self._last_periods) == 0:
            return np.nan
        return sum(self._last_periods) / len(self._last_periods)

    def get_estimated_frequency(self):
        """Estimated frequency in Hz."""
        return self._fs / self.get_estimated_period()






### ------------------- Test that it works properly ---------------------------

if __name__ == '__main__':
    import numpy.random
    import scipy.signal as ssi
    import matplotlib.pyplot as plt

    # Send a chirp with some noise, and try to recover its frequency

    # Input signal
    f0 = 50
    f1 = 1000
    t = np.arange(0, 10, 1/44100)
    ft = f0 * (f1/f0)**(t/max(t))
    chirp = ssi.chirp(t, f0, max(t), f1, method='log')
    noise_lv = 0.1
    chirp += numpy.random.randn(len(chirp)) * noise_lv

    # Slicing the signal
    N = 256 # slice size
    sliced = [chirp[N*k:N*(k+1)] for k in range(int(len(chirp)/N))]
    f_correct = [ft[N*k] for k in range(int(len(chirp)/N))]

    # Getting the estimation
    pf = PeriodFinder()
    f_estimates = []
    for slice_ in sliced:
        f_estimates.append(pf(slice_))

    # Comparison
    plt.loglog(f_correct, f_estimates)
    plt.loglog(f_correct, f_correct)

