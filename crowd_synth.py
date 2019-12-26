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
                 nb_synths=100,
                 **kwargs):
        frequencies = frequency * (1 + randn(nb_synths)/24)
        volumes = volume * random(nb_synths)
        volumes /= np.sum(volumes)
        self._subsynths = [OneNoteSynth(f, v, *args, **kwargs)
                            for f, v in zip(frequencies, volumes)]
        self.is_alive = True

    def get_data(self, frames):
        data = np.zeros(frames)
        for sub in self._subsynths:
            data += sub.get_data(frames)
        self.is_alive = any(sub.is_alive for sub in self._subsynths)
        return data

    def note_off(self):
        for sub in self._subsynths:
            sub.note_off()

class CrowdSynth(PolyphonicSynth):
    def __init__(self, waveform, envelope,
                 nb_synths=100, **kwargs):
        super().__init__(**kwargs)
        self._waveform, self._envelope = waveform, envelope
        self._nb_synths = nb_synths

    def create_note(self, note_number, velocity):
        return CrowdSynthNote(freq_of_note(note_number), velocity/128,
                                  self._waveform, self._envelope,
                                  nb_synths=self._nb_synths)


CROWD_SYNTH = CrowdSynth(OFFSET_TRI_02, ORGAN_ENVELOPE)

if __name__ == '__main__':
    import sounddevice as sd
    import mido


    synth = CROWD_SYNTH

    def callback(indata, outdata, frames, time, status):
        outdata[:, 0] = synth.get_data(frames)

    with sd.Stream(samplerate=SAMPLERATE, channels=1, callback=callback):
        with mido.open_input() as inport:
            inport.callback = synth.receive
            while not inport.closed:
                time.sleep(0.1)
