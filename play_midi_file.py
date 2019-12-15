# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 21:37:38 2019

@author: User
"""
import mido
import sounddevice as sd

from synth import ORGAN_SYNTH, SAMPLERATE

def play_midi_file(filename, synth):
    mid = mido.MidiFile(filename)
    
    
    def callback(indata, outdata, frames, time, status):
        outdata[:, 0] = synth.get_data(frames)
        
    with sd.Stream(samplerate=SAMPLERATE, channels=1, callback=callback):
        for msg in mid.play():
            synth.receive(msg)



if __name__ == '__main__':
    filename = 'Dejected_Groose_piano.mid'
    print("Playing", filename, "with ORGAN_SYNTH")
    play_midi_file(filename, ORGAN_SYNTH)
    
    