from jchord.knowledge import MAJOR_FROM_C, MAJOR_SCALE_OFFSETS
from jchord.core import Note, split_to_base_and_shift


class InvalidNote(Exception):
    pass


def get_midi(note: Note) -> int:
    c0_code = 12
    name, octave = note
    name, shift = split_to_base_and_shift(name, name_before_accidental=True)
    for candidate, offset in zip(MAJOR_FROM_C, MAJOR_SCALE_OFFSETS.values()):
        if name == candidate:
            return c0_code + offset + shift + 12 * octave
    raise InvalidNote(name)


def midi_to_pitch(midi: int) -> float:
    return 440 * (2 ** ((midi - 69) / 12))
