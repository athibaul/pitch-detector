#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 17:06:37 2019

@author: alexis
"""
import numpy as np
import sounddevice as sd
from periodfinder import PeriodFinder

#duration = 5.5  # seconds

pf = PeriodFinder()

def callback(indata, outdata, frames, time, status):
    if status:
        print(repr(status))
    mono = np.sum(indata, axis=1)
    f = pf(mono)
    print(f)

with sd.Stream(channels=2, callback=callback):
    while True:
        sd.sleep(100)
