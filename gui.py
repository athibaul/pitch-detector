# -*- coding: utf-8 -*-
"""
The user interface : a circle displaying the note being sung.

Created on Mon Nov 18 21:15:55 2019

@author: Alexis THIBAULT
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import collections

class PitchGUI:
    def __init__(self, fs=44100, blocksize=256, persistence=0.1):
        self.freqs = collections.deque([], int(persistence*fs/blocksize))
        self._init_plot()
        
    def _init_plot(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_aspect('equal')
        self.ax.set_xlim((-1.5, 1.5))
        self.ax.set_ylim((-1.5, 1.5))
        self._draw_background()
        self._points, = self.ax.plot([], [], 'o')
        
        self.animation = FuncAnimation(self.fig, self.animate, interval=30)
        
    def _draw_background(self):
        note_names = ['A', 'A#/Bb', 'B', 'C', 'C#/Db', 'D',
                      'D#/Eb', 'E', 'F', 'F#/Gb', 'G', 'G#/Ab']
        for i, name in zip(range(12), note_names):
            theta = 2 * np.pi * i / 12
            ct, st = np.cos(theta), np.sin(theta)
            xx = [0, ct]
            yy = [0, st]
            self.ax.plot(xx, yy, '-k')
            self.ax.annotate(name, (ct, st), (ct*1.2, st*1.2))
            
        
    def _create_points(self):
        freqs = np.array(self.freqs)
        notes = 12 * np.log2(freqs/440)
        theta = 2*np.pi / 12 * notes
        xx = np.cos(theta)
        yy = np.sin(theta)
        return xx, yy
    
    def give_frequency(self, f):
        self.freqs.append(f)
        
    def animate(self, frame):
        self._points.set_data(*self._create_points())
        return self._points,
    
    
