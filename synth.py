# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 16:45:23 2019

@author: User
"""
import collections
import threading
import abc

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

        self.is_alive = True

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
            self.is_alive = False
            result = np.zeros(frames)
        self._cur_level = result[-1]
        self._t = next_t
        return result


    def note_off(self):
        """Begin the 'release' phase of the note."""
        self._released = True
        self._release_volume = self._cur_level
        self._t = 0


DEFAULT_ENVELOPE = Envelope(1e-3, 1e-3, 1.0, 1e-3)
TEST_ENVELOPE = Envelope(0.1, 0.2, 0.3, 0.4)


SAWTOOTH_WAVE = lambda x: 2*x-1
TRIANGLE_WAVE = lambda x: 4*abs(x-1/2)-1
SINE_WAVE = lambda x: np.sin(2*np.pi*x)
SQUARE_WAVE = lambda x: 1.0*(x<1/2) - 1.0*(x>1/2)
def offset_triangle(alpha=0.2):
    return lambda x: (x<alpha)*(2*x/alpha - 1) \
        + (x>alpha) * (1-2*(x-alpha)/(1-alpha))
OFFSET_TRI_02 = offset_triangle(0.2)
OFFSET_TRI_01 = offset_triangle(0.1)

def freq_of_note(note):
    """Convert MIDI note number to frequency in Hertz."""
    return 440 * 2**((note-69)/12)


class Synth(abc.ABC):
    @abc.abstractmethod
    def get_data(self, frames):
        """Get the next `frames` frames of data output by this synth.

        Parameters
        ----------
        frames : int
            Number of frames of data to read.

        Returns
        -------
        data : np.array
            Array of length `frames`."""


class NullSynth(Synth):
    def get_data(self, frames):
        return np.zeros(frames)


class OneNoteSynth(Synth):

    def __init__(self, frequency, volume, waveform, envelope,
                 fm=NullSynth(), fm_strength=1.0):
        self._envelope = EnvelopeGain(envelope)
        self._waveform = waveform
        self._volume = volume
        self._frequency = frequency
        self._fm = fm
        self._fm_strength = fm_strength
        self._t_norm = 0.0
        self.is_alive = True

    def set_fm_strength(self, fm_strength):
        self._fm_strength = fm_strength

    def get_data(self, frames):
        data = self._create_wave_data(frames) * self._envelope.get_gain(frames)
        self.is_alive = self._envelope.is_alive
        return data * self._volume

    def _create_wave_data(self, frames):
#        tt = self._t + np.arange(frames)/SAMPLERATE
#        tt_norm = (tt * self._frequency) % 1
#        self._t += frames/SAMPLERATE
        fm_data = self._fm_strength * self._fm.get_data(frames)
        tt_norm = self._t_norm + np.cumsum(self._frequency * (1 + fm_data))/SAMPLERATE
        tt_norm %= 1.0
        self._t_norm = tt_norm[-1]
        return self._waveform(tt_norm)

    def note_off(self):
        self._envelope.note_off()

class PolyphonicSynth(Synth, metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def create_note(self, note_number, velocity):
        pass

    def __init__(self, max_polyphony=10, gain=0.1):
        self.note_synths = collections.OrderedDict()
        self.note_synths_dying = []
        self.max_polyphony = max_polyphony
        self.gain = gain
        self._lock = threading.Lock()

        self._t = 0.0

    def all_note_synths(self):
        with self._lock:
            yield from iter(self.note_synths.values())
            yield from iter(self.note_synths_dying)

    def receive(self, msg):
        print(msg)
        if msg.type == 'note_on' and msg.velocity > 0:
            self.note_on(msg.note, msg.velocity)
        elif msg.type == 'note_on' and msg.velocity == 0 \
            or msg.type == 'note_off':
            self.note_off(msg.note)
        self.bury_dead_notes()

    def get_time(self):
        """Get current time according to the number of samples sent.

        Precision is of the order of the audio block size,
        so frames/SAMPLERATE.
        """
        return self._t

    def note_on(self, note, velocity):
        # Don't let the same note play twice at the same time.
        self.note_off(note)

        # Don't let more than `max_polyphony` notes
        # play at the same time.
        if len(self.note_synths) >= self.max_polyphony:
            note_to_kill = next(iter(self.note_synths))
            self.note_off(note_to_kill)

        note_synth = self.create_note(note, velocity)

        with self._lock:
            self.note_synths[note] = note_synth

    def note_off(self, note):
        with self._lock:
            try:
                prev_note = self.note_synths.pop(note)
                prev_note.note_off()
                self.note_synths_dying.append(prev_note)
            except KeyError:
                pass

    def get_data(self, frames):
        datas = [note_synth.get_data(frames) for note_synth in self.all_note_synths()]
        self._t += frames/SAMPLERATE
        return np.sum(datas, axis=0) * self.gain

    def bury_dead_notes(self):
        with self._lock:
            self.note_synths_dying = list(filter(
                    lambda note_synth: note_synth.is_alive,
                    self.note_synths_dying))

class SimplePolySynth(PolyphonicSynth):
    def __init__(self, waveform, envelope, **kwargs):
        super().__init__(**kwargs)
        self._waveform, self._envelope = waveform, envelope

    def create_note(self, note_number, velocity):
        return OneNoteSynth(freq_of_note(note_number), velocity/128,
                                  self._waveform, self._envelope)


class FMSynth(PolyphonicSynth):
    """Synth with one level of Frequency Modulation."""
    def __init__(self, envelope=DEFAULT_ENVELOPE,
                 envelope_fm=DEFAULT_ENVELOPE,
                 fm_strength=1.0,
                 velocity_influences_fm=True,
                 **kwargs):
        super().__init__(**kwargs)
        self._envelope = envelope
        self._envelope_fm = envelope_fm
        self._fm_strength = fm_strength
        self._velocity_influences_fm = velocity_influences_fm

    def receive(self, msg):
        super().receive(msg)
        if msg.type == 'control_change' and msg.control == 7:
            self.set_fm_strength(msg.value/128.0 * 15.0)

    def set_fm_strength(self, fm_strength):
        self._fm_strength = fm_strength
        for synth in self.all_note_synths():
            synth.set_fm_strength(fm_strength)

    def create_note(self, note_number, velocity):
        freq = freq_of_note(note_number)
        child_volume = velocity/128 if self._velocity_influences_fm else 1.0
        fm_synth = OneNoteSynth(freq, child_volume,
                                SINE_WAVE, self._envelope_fm)
        return OneNoteSynth(freq, velocity/128, SINE_WAVE, self._envelope,
                 fm=fm_synth, fm_strength=self._fm_strength)



BASS_ENVELOPE = Envelope(1e-4, 0.1, 0.8, 1e-3)
BASS_SYNTH = SimplePolySynth(SAWTOOTH_WAVE, BASS_ENVELOPE, max_polyphony=1)

ORGAN_ENVELOPE = Envelope(0.05, 0.5, 0.8, 0.2)
ORGAN_SYNTH = SimplePolySynth(OFFSET_TRI_01, ORGAN_ENVELOPE)

NO_ENVELOPE = Envelope(1e-3, 1e-3, 1.0, 1e-3)
CHIPTUNE = SimplePolySynth(SQUARE_WAVE, NO_ENVELOPE)

SIMPLE_FM_SYNTH = FMSynth(ORGAN_ENVELOPE,
                          NO_ENVELOPE,
                          fm_strength=5.0,
                          velocity_influences_fm=False)

if __name__ == '__main__':
    import sounddevice as sd
    import mido
    import time


    synth = SIMPLE_FM_SYNTH

    def callback(indata, outdata, frames, time, status):
        outdata[:, 0] = synth.get_data(frames)

    with sd.Stream(samplerate=SAMPLERATE, channels=1, callback=callback):
        with mido.open_input() as inport:
            inport.callback = synth.receive
            while not inport.closed:
                time.sleep(0.1)
