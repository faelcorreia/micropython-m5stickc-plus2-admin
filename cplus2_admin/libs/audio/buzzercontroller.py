"""
MIT license
Copyright (c) 2024 Rafael Correia
https://github.com/faelcorreia/micropython-m5stickc-plus2-admin
"""

from machine import PWM  # type: ignore
import re
from libs.audio.notes import NOTES
import time


class BuzzerController:
    MAXIMUM_DUTY = 512

    def __init__(self, buzzer: PWM) -> None:
        self.buzzer = buzzer
        self.note_regex = re.compile(r"^([A-G][#b]?[0-9]|_|~)$")

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

    def __set_volume(self, volume: int):
        if volume >= 0 and volume <= 100:
            duty = round((volume / 100) * self.MAXIMUM_DUTY)
            self.buzzer.duty(duty)

    def __set_freq(self, freq: int):
        self.buzzer.freq(freq)

    def __start(self):
        self.buzzer.init()

    def __stop(self):
        self.buzzer.deinit()

    def play_notes(self, bpm: int, step: int, notes: list[str]):
        self.__start()
        note_us = min(round((60 / bpm * 1000) / (step / 4)), 4000) * 1000
        total_notes = len(notes)
        for i in range(total_notes):
            note = notes[i]
            if self.note_regex.match(note):
                if note == "_":
                    self.__set_volume(0)
                elif note != "~":
                    freq = self.note_to_freq(note)
                    self.__set_volume(100)
                    self.__set_freq(round(freq))
            else:
                raise Exception(f"Wrong note: {note}")
            if note_us > 0:
                time.sleep_us(note_us)
        self.__stop()
