# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 16:45:23 2019

@author: User
"""
import collections

import numpy as np

SAMPLERATE = 44100

class NoteFinished(Exception):
    """Exception raised when a Note cannot send any more data."""
    pass

Envelope = collections.namedtuple('Envelope', ['a', 'd', 's', 'r'])

class EnvelopeGain:
    def __init__(self, envelope):
        self._env = envelope
        self.attack, self.decay, self.sustain, self.release = self._env
        self._cur_level = 0.0
        self._released = False
        self._t = 0
    
    def get_gain(self, frames):
        """Get the next `frames` frames of the gain.
        
        frames : int.
        returns : an array of length `frames`
        raises : NoteFinished
        """
        tt = np.arange(frames)/SAMPLERATE + self._t
        next_t = frames/SAMPLERATE + self._t
        if not self._released and self._t < self.attack + self.decay:
            atk_mask = (tt < self.attack)
            decay_mask = ~atk_mask & (tt < self.attack + self.decay)
            sustain_mask = ~atk_mask & ~decay_mask
            atk = tt / self.attack
            decay = 1 + (tt - self.attack) * (self.sustain-1) / self.decay
            sustain = self.sustain
            result = atk_mask*atk + decay_mask*decay + sustain_mask*sustain
        elif not self._released:
            result = self.sustain * np.ones(frames)
        elif self._t < self.release:
            release_mask = tt < self.release
            release = (1 - tt/self.release)*self._release_volume
            result = release_mask*release
        else:
            raise NoteFinished()
        self._cur_level = result[-1]
        self._t = next_t
        return result
        
        
    def turn_off(self):
        """Begin the 'release' phase of the note."""
        self._released = True
        self._release_volume = self._cur_level
        self._t = 0
    

DEFAULT_ENVELOPE = Envelope(1e-3, 0.0, 1.0, 1e-3)
# TEST_ENVELOPE = Envelope(0.1, 0.2, 0.3, 0.4)


class OneNoteSynth:
    
    def __init__(self, frequency, volume, waveform, envelope):
        pass
    
    