#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 17:06:37 2019

@author: alexis
"""
import sounddevice as sd

duration = 5.5  # seconds

def callback(indata, outdata, frames, time, status):
    if status:
        print(repr(status))
    print(len(indata), len(outdata))
    outdata[:] = indata

with sd.Stream(channels=2, callback=callback):
    sd.sleep(int(duration * 1000))
