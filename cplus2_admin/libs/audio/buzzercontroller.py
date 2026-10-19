"""
MIT license
Copyright (c) 2024-2026 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin
"""

from machine import PWM  # type: ignore
import re
from libs.audio.notes import NOTES
import libs.std.time as time


class BuzzerController:
    """Non-blocking player for the passive buzzer.

    ``play_notes`` only builds the playlist and returns immediately. The main
    loop must call ``process`` so notes advance while the web server keeps
    answering requests.
    """

    MAXIMUM_DUTY = 512
    SILENCE = "_"
    EXTEND = "~"

    def __init__(self, buzzer: PWM) -> None:
        self.buzzer = buzzer
        self.note_regex = re.compile(r"^([A-G][#b]?[0-9]|_|~)$")
        self._playlist = []
        self._index = 0
        self._playing = False
        self._note_started_us = 0

    def note_to_freq(self, note: str) -> float:
        key = note[0]
        if note[1] == "#":
            key += "_SHARP"
            octave = note[2]
        elif note[1] == "b":
            key += "_FLAT"
            octave = note[2]
        else:
            octave = note[1]
        octave = int(octave)
        return NOTES[key][octave]

    def play_notes(self, bpm: int, step: int, notes: list[str]) -> int:
        """Validate the song, start playing it and return the note count."""
        if bpm <= 0 or step <= 0:
            raise ValueError("BPM and step must be greater than zero")

        note_us = min(round((60 / bpm * 1000) / (step / 4)), 4000) * 1000
        if note_us <= 0:
            raise ValueError("Song is too fast to play")

        playlist = []
        for note in notes:
            if not self.note_regex.match(note):
                raise ValueError(f"Wrong note: {note}")
            if note == self.EXTEND:
                if playlist:
                    freq, duration = playlist[-1]
                    playlist[-1] = (freq, duration + note_us)
                else:
                    playlist.append((None, note_us))
            elif note == self.SILENCE:
                playlist.append((None, note_us))
            else:
                playlist.append((self.note_to_freq(note), note_us))

        if not playlist:
            raise ValueError("No notes to play")

        self.stop()
        self._playlist = playlist
        self._index = 0
        self._note_started_us = time.ticks_us()
        self._playing = True
        self.buzzer.init()
        self._start_current_note()
        return len(playlist)

    def process(self):
        """Advance playback. Must be called regularly from the main loop."""
        if not self._playing:
            return

        now = time.ticks_us()
        while self._playing:
            duration = self._playlist[self._index][1]
            if time.ticks_diff(now, self._note_started_us) < duration:
                break

            self._note_started_us = time.ticks_add(self._note_started_us, duration)
            self._index += 1
            if self._index >= len(self._playlist):
                self.stop()
                break
            self._start_current_note()

    def stop(self):
        if self._playing:
            self.buzzer.duty(0)
            self.buzzer.deinit()
        self._playing = False
        self._playlist = []
        self._index = 0

    def is_playing(self) -> bool:
        return self._playing

    def remaining_ms(self) -> int:
        if not self._playing:
            return 0
        remaining_us = 0
        for index in range(self._index, len(self._playlist)):
            remaining_us += self._playlist[index][1]
        elapsed_us = time.ticks_diff(time.ticks_us(), self._note_started_us)
        return max(0, (remaining_us - elapsed_us) // 1000)

    def _start_current_note(self):
        freq = self._playlist[self._index][0]
        if freq is None:
            self.buzzer.duty(0)
        else:
            self.buzzer.freq(round(freq))
            self.buzzer.duty(self.MAXIMUM_DUTY)
