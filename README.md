# pitch-detector

A small project to detect the pitch of sung voice.

Needs `scipy >= 1.2.0` and `sounddevice`.

Main script is the (badly-named) `sounddevice_test.py`. It's not working too well.



Also in this repository are found several
# mini-synths
The mini-synths need `mido`.

* `mido_test.py` contains a minimal synth that receives MIDI events from the default MIDI device, and plays sine waves.
* `synth.py` is a bit more advanced, as that synth can play polyphony, and has configurable waveform (periodic function) and envelope (attack/decay/sustain/release).
* `play_midi_file.py` plays an example MIDI file using the `ORGAN_SYNTH` from `synth.py`.
