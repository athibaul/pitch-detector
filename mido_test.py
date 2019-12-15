# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 10:22:04 2019

@author: Alexis
"""
import time

import numpy as np
import mido
import sounddevice as sd

SAMPLERATE = 44100
TWO_PI = 2 * np.pi



class Synth:
    """A basic sine-wave monophonic synth.
    
    Receives MIDI events, and plays through a mono stream.
    """
    
    def __init__(self):
        self._phase = 0
        self._dt = 1/SAMPLERATE
        self._note = None
        self._omega = 0.0  # 2 * pi * frequency
        self._amplitude = 0.0
    
    def receive(self, msg):
        """Receive MidiEvent."""
        print("Received MIDI Event :", msg)
        if msg.type == 'note_on' and msg.velocity > 0:
            self._set_note(msg.note)
            self._set_velocity(msg.velocity)
        elif msg.type == 'note_on' and msg.velocity == 0:
            # Only take into account note_off if it is for the current note
            if self._note == msg.note:
                self._set_velocity(0)
    
    def _set_note(self, note):
        semitones = note - 69  # Distance from A440
        self._note = note
        self._omega = TWO_PI * 440 * 2.0**(semitones/12.0)
        
    def _set_velocity(self, velocity):
        self._amplitude = velocity / 128
    
    def callback(self, indata, outdata, frames, time, status):
        """Put data on `outdata`."""
        phases = np.arange(frames)*self._dt * self._omega + self._phase
        outdata[:, 0] = self._amplitude * np.sin(phases)
        self._phase = (self._phase + frames*self._dt*self._omega) % TWO_PI

        
synth = Synth()



if __name__ == '__main__':
    print("Available MIDI inputs are:", mido.get_input_names())
    with sd.Stream(samplerate=SAMPLERATE, channels=1, callback=synth.callback):
        with mido.open_input() as inport:
            inport.callback = synth.receive
            while not inport.closed:
                time.sleep(0.1)
            
        