import sounddevice as sd
import numpy as np
import scipy.signal as ssi
import matplotlib.pyplot as plt
duration = 5.5  # seconds

def callback(indata, outdata, frames, time, status):
    if status:
        print(repr(status))
    print(len(indata), len(outdata))
    outdata[:] = indata

def lowpass_filter(fc, order=6, fs=44100):
    b, a = ssi.butter(order, fc, btype='lowpass', fs=fs)
    z_values = [0]*order
    def filter_(indata):
        nonlocal z_values
        outdata, z_values = ssi.lfilter(b, a, indata, zi=z_values)
        return outdata
    return filter_

def bandpass_filter(f_low=50, f_high=1000, order=6, fs=44100):
    sos = ssi.iirfilter(order, (f_low, f_high), btype='band', fs=fs, output='sos')
    z_values = np.zeros((sos.shape[0], 2))
    def filter_(indata):
        nonlocal z_values
        outdata, z_values = ssi.sosfilt(sos, indata, zi=z_values)
        return outdata
    return filter_

#def bandpass_filter_ba(f_low=40, f_high=1000, order=4, fs=44100):
#    """WARNING : Unstable for order > 5."""
#    b, a = ssi.iirfilter(order, (f_low, f_high), btype='band', fs=fs, output='ba')
#    z_values = np.zeros(len(b) - 1)
#    def filter_(indata):
#        nonlocal z_values
#        outdata, z_values = ssi.lfilter(b, a, indata, zi=z_values)
#        return outdata
#    return filter_


def bandpass_and_integrate(f_low=50, f_high=1000, order=6, fs=44100):
    sos_1 = ssi.iirfilter(order, (f_low, f_high), btype='band', fs=fs, output='sos')
    sos_2 = ssi.iirfilter(1, f_low, btype='low', fs=fs, output='sos')
    sos = np.concatenate((sos_1, sos_2), axis=0)
    z_values = np.zeros((sos.shape[0], 2))
    def filter_(indata):
        nonlocal z_values
        outdata, z_values = ssi.sosfilt(sos, indata, zi=z_values)
        return outdata
    return filter_


def test_filter(filt, f0=20, f1=20000):
    t = np.arange(0, 5, 1/44100)
    chirp = ssi.chirp(t, f0, max(t), f1, method='log')
    #plt.plot(t, chirp)
    ft = f0 * (f1/f0)**(t/max(t))
    filtered = filt(chirp)
    plt.semilogx(ft, filtered)
    assert np.all(np.isfinite(filtered))


test_filter(lowpass_filter(1000, 6))
test_filter(lowpass_filter(250))


if __name__ == '__main__':
    test_filter(bandpass_filter())
    test_filter(bandpass_and_integrate())




#
#with sd.Stream(channels=2, callback=callback):
#    sd.sleep(int(duration * 1000))
