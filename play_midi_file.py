# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 21:37:38 2019

@author: User
"""
import mido
import sounddevice as sd
import time

from synth import *



class MidiFilePlayer:
    def __init__(self, filename, msg_handler, timer):
        """
        filename : str
            Midi file to play
        msg_handler : callable(MidiMessage)
            Called to handle each MidiMessage in real time
        timer : callable
            Called to get the current time in seconds.
            Should be as precise as possible.
        """
        self.mid = mido.MidiFile(filename)
        self.msg_handler = msg_handler
        self.iterator = self.callback_iterator()
        self.timer = timer

        self.finished = False

    def callback_iterator(self):
        for msg in self.mid:
            self.last_note_ns = self.timer()
            while (self.timer() - self.last_note_ns) < msg.time:
                yield
            self.msg_handler(msg)

            elapsed =  (self.timer() - self.last_note_ns)
            err = elapsed - msg.time
            if err > 0.003:
                print("Oops! I'm {:.3f}s late".format(err))

    def callback(self):
        """Call this often. Checks if we should send any MidiMessage now."""
        try:
            next(self.iterator)
        except StopIteration:
            self.finished = True


def play_midi_file(filename, synth):

    player = MidiFilePlayer(filename,
                            msg_handler=synth.receive,
                            timer=synth.get_time)

    def callback(indata, outdata, frames, time, status):
        outdata[:, 0] = synth.get_data(frames)
        player.callback()

    with sd.Stream(samplerate=SAMPLERATE, channels=1, callback=callback, blocksize=128):
        while not player.finished:
            time.sleep(1)



if __name__ == '__main__':
    filename = 'Dejected_Groose_piano.mid'
    print("Playing", filename, "with ORGAN_SYNTH")
    play_midi_file(filename, SIMPLE_FM_SYNTH)

