"""
Create filters for sampled digital signal.
"""


import numpy as np
import scipy.signal as ssi
import matplotlib.pyplot as plt

class Filter:
    """A digital filter, to be applied to a digital signal.

    In case of sequential calls, the filter should behave as if the signals were
    concatenated, unless reset() is called in-between.


    You should call filter_(signal) where signal is array-like and sampled at fs.
    Should be a morphism for concatenation : concat(filter_(a), filter_(b)) is close to filter_(concat(a,b))
    """

    def __init__(self, sos):
        self.sos = sos
        self.reset()

    def reset(self):
        self._z_values = np.zeros((self.sos.shape[0], 2))

    def __call__(self, indata):
        outdata, self._z_values = ssi.sosfilt(self.sos,
                                             indata,
                                             zi=self._z_values)
        return outdata



### ---------- Factory functions ---------------------------

def lowpass_filter(fc, order=6, fs=44100):
    sos = ssi.butter(order, fc, btype='lowpass', fs=fs, output='sos')
    return Filter(sos)

def bandpass_filter(f_low=50, f_high=1000, order=6, fs=44100):
    sos = ssi.iirfilter(order, (f_low, f_high), btype='band', fs=fs, output='sos')
    return Filter(sos)

def bandpass_and_integrate(f_low=50, f_high=1000, order=6, fs=44100):
    """Create a filter that is a combination of a band-pass of order `order`
    and a low-pass of order 1.
    """
    sos_1 = ssi.iirfilter(order, (f_low, f_high), btype='band', fs=fs, output='sos')
    sos_2 = ssi.iirfilter(1, f_low, btype='low', fs=fs, output='sos')
    sos = np.concatenate((sos_1, sos_2), axis=0)
    return Filter(sos)





### ------------------- Test that it works properly ---------------------------

if __name__ == '__main__':

    def test_filter(filt, f0=20, f1=20000):
        t = np.arange(0, 5, 1/44100)
        chirp = ssi.chirp(t, f0, max(t), f1, method='log')
        ft = f0 * (f1/f0)**(t/max(t))
        filtered = filt(chirp)

        first_half = t < 2
        second_half = t >= 2
        chirp1 = chirp[first_half]
        chirp2 = chirp[second_half]
        filt.reset()
        filtered1 = filt(chirp1)
        filtered2 = filt(chirp2)

        plt.semilogx(ft, filtered)

        # No divergence
        assert np.all(np.isfinite(filtered))

        # Morphism for concatenation
        assert np.allclose(np.concatenate((filtered1, filtered2)), filtered)

    test_filter(lowpass_filter(1000, 6))
    test_filter(lowpass_filter(250))
    test_filter(bandpass_filter())
    test_filter(bandpass_and_integrate())


