#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 17:06:37 2019

@author: alexis
"""
import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
from periodfinder import PeriodFinder
from gui import PitchGUI

#duration = 5.5  # seconds

pf = PeriodFinder()
gui = PitchGUI()

def callback(indata, outdata, frames, time, status):
    if status:
        print(repr(status))
    mono = np.sum(indata, axis=1)
    f = pf(mono)
    gui.give_frequency(f)
    # print(f)

with sd.Stream(channels=2, callback=callback, blocksize=256):
    while plt.fignum_exists(gui.fig.number):
        plt.pause(0.5)
