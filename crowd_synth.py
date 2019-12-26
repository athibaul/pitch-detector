# -*- coding: utf-8 -*-
"""
Created on Thu Dec 26 18:56:18 2019

@author: User
"""
import numpy as np
from numpy.random import randn, random

from synth import (Synth, OneNoteSynth, SAMPLERATE, PolyphonicSynth,
                   freq_of_note, OFFSET_TRI_02, ORGAN_ENVELOPE)

class CrowdSynthNote(Synth):
    """Simulate a crowd of synths with randomized volumes/pitches."""
    def __init__(self, frequency, volume, *args,
                 nb_synths, freq_width=1/100,
                 **kwargs):
        frequencies = frequency * (1 + randn(nb_synths) * freq_width)
#        frequencies = frequency * \
#                        (1 + np.linspace(-1, 1, nb_synths)*freq_width)
        volumes = volume * random(nb_synths)
        volumes /= np.sum(volumes)
        self._subsynths = [OneNoteSynth(f, v, *args, **kwargs)
                            for f, v in zip(frequencies, volumes)]
        self._pannings = random(nb_synths)*2 - 1.0
        self.is_alive = True

    def get_data(self, frames):
        """Returns stereo data"""
        data = np.zeros((frames, 2))
        for sub, panning in zip(self._subsynths, self._pannings):
            data += pan(sub.get_data(frames), panning)
        self.is_alive = any(sub.is_alive for sub in self._subsynths)
        return data

    def note_off(self):
        for sub in self._subsynths:
            sub.note_off()

class CrowdSynth(PolyphonicSynth):
    def __init__(self, waveform, envelope,
                 nb_synths=50, **kwargs):
        super().__init__(**kwargs)
        self._waveform, self._envelope = waveform, envelope
        self._nb_synths = nb_synths

    def create_note(self, note_number, velocity):
        return CrowdSynthNote(freq_of_note(note_number), velocity/128,
                                  self._waveform, self._envelope,
                                  nb_synths=self._nb_synths)


CROWD_SYNTH = CrowdSynth(OFFSET_TRI_02, ORGAN_ENVELOPE)



def pan(data, panning=0.0):
    """Convert mono data to stereo with panning.

    data : array of shape (frames,)
    panning : float in [-1.0, 1.0]
        Left is -1.0, right is 1.0

    Returns
    -------
    out_data : array of shape (frames, 2)
    """
    frames = len(data)
    assert data.shape == (frames,)
    panning = max(-1.0, min(panning, 1.0)) # Clip to [-1.0, 1.0]

    left_gain = (1-panning)/2
    right_gain = 1-left_gain
    out_data = np.zeros((frames, 2))
    out_data[:, 0] = left_gain * data
    out_data[:, 1] = right_gain * data
    return out_data


if __name__ == '__main__':
    import time
    import sounddevice as sd
    import mido


    synth = CROWD_SYNTH

    def callback(indata, outdata, frames, time, status):
        outdata[:] = synth.get_data(frames)

    with sd.Stream(samplerate=SAMPLERATE, channels=2, callback=callback):
        with mido.open_input() as inport:
            inport.callback = synth.receive
            while not inport.closed:
                time.sleep(0.1)
