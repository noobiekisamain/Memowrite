"""Beeps, notes, sound files and talking."""

import os
import subprocess
import sys
import threading
import time

from ..errors import MemoError

NOTES = {"c": 261.63, "c#": 277.18, "d": 293.66, "d#": 311.13, "e": 329.63, "f": 349.23, "f#": 369.99,
         "g": 392.0, "g#": 415.3, "a": 440.0, "a#": 466.16, "b": 493.88}


def _winsound():
    if os.name != "nt":
        return None
    import winsound
    return winsound


def beep(it, times=1):
    ws = _winsound()
    for i in range(max(1, times)):
        if i:
            time.sleep(0.25)
        if ws:
            ws.MessageBeep(ws.MB_OK)
        else:
            it.write("\a")


def note_frequency(name):
    """'a', 'c#', 'g5' -> frequency"""
    name = str(name).lower().strip()
    octave = 4
    if name and name[-1].isdigit():
        octave = int(name[-1])
        name = name[:-1]
    if name not in NOTES:
        raise MemoError(f"I don't know the note '{name}'. Use c, d, e, f, g, a, b (and # for sharp)")
    return NOTES[name] * (2 ** (octave - 4))


def tone(it, freq, ms):
    if isinstance(freq, str):
        freq = note_frequency(freq)
    ws = _winsound()
    freq = int(max(37, min(32767, freq)))
    ms = int(max(1, ms))
    if ws:
        ws.Beep(freq, ms)
    else:
        time.sleep(ms / 1000)


def play(it, path, loop=False):
    if not os.path.exists(path):
        raise MemoError(f"I can't find the sound file '{os.path.basename(path)}'")
    ws = _winsound()
    if ws and path.lower().endswith(".wav"):
        flags = ws.SND_FILENAME | ws.SND_ASYNC
        if loop:
            flags |= ws.SND_LOOP
        ws.PlaySound(path, flags)
        return
    if os.name == "nt":
        # mp3 and others: use the Windows media player engine, quietly
        script = ("Add-Type -AssemblyName presentationCore; $p = New-Object system.windows.media.mediaplayer; "
                  f"$p.open('{path}'); $p.Play(); Start-Sleep -s 1; "
                  "while($p.NaturalDuration.HasTimeSpan -eq $false){Start-Sleep -m 100}; "
                  "Start-Sleep -s $p.NaturalDuration.TimeSpan.TotalSeconds")
        proc = subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", script],
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        it._sound_proc = proc
        return
    it.write(f"(playing {os.path.basename(path)})\n")


def stop(it):
    ws = _winsound()
    if ws:
        ws.PlaySound(None, 0)
    proc = getattr(it, "_sound_proc", None)
    if proc is not None:
        try:
            proc.kill()
        except Exception:
            pass


def speak(it, text):
    if os.name == "nt":
        safe = text.replace("'", "''")
        script = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')"
        subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        it.write(f"(speaking) {text}\n")
