import itertools
from collections import namedtuple
from typing import Hashable

from jchord.knowledge import MAJOR_SCALE_OFFSETS, CHROMATIC

Note = namedtuple("Note", "name octave")


class InvalidDegree(Exception):
    pass


def split_to_base_and_shift(
    name_or_degree: str, name_before_accidental: bool
) -> (str, int):
    if "b" in name_or_degree and "#" in name_or_degree:
        raise InvalidDegree("Both sharp and flat in degree")

    shift = 0
    if name_before_accidental:
        while name_or_degree.endswith("b"):
            shift -= 1
            name_or_degree = name_or_degree[:-1]
        while name_or_degree.endswith("#"):
            shift += 1
            name_or_degree = name_or_degree[:-1]
    else:
        while name_or_degree.startswith("b"):
            shift -= 1
            name_or_degree = name_or_degree[1:]
        while name_or_degree.startswith("#"):
            shift += 1
            name_or_degree = name_or_degree[1:]
    return name_or_degree, shift


def degree_to_semitone(degree: str) -> int:
    degree, shift = split_to_base_and_shift(degree, name_before_accidental=False)

    # Now the remaining string should be an int
    try:
        int_degree = int(degree)
    except ValueError:
        raise InvalidDegree(degree)

    # Consider one octave above
    if int_degree > 7:
        int_degree -= 7
        shift += 12

    # Return
    try:
        return MAJOR_SCALE_OFFSETS[int_degree] + shift
    except KeyError as error:
        raise InvalidDegree(degree) from error


def shift_up(note: Note) -> Note:
    name, octave = note
    for i, other in enumerate(CHROMATIC):
        if name == other:
            if i == len(CHROMATIC) - 1:
                return Note(name=CHROMATIC[0], octave=octave + 1)
            else:
                return Note(name=CHROMATIC[i + 1], octave=octave)


def shift_down(note: Note) -> Note:
    name, octave = note
    for i, other in enumerate(CHROMATIC):
        if name == other:
            if i == 0:
                return Note(name=CHROMATIC[-1], octave=octave - 1)
            else:
                return Note(name=CHROMATIC[i - 1], octave=octave)


def transpose(note: Note, shift: int) -> Note:
    if shift > 0:
        for _ in itertools.repeat(None, shift):
            note = shift_up(note)
    else:
        for _ in itertools.repeat(None, -shift):
            note = shift_down(note)
    return note


def note_diff(name_low: str, name_high: str) -> int:
    diff = 0
    note = Note(name_low, 0)
    while note.name != name_high:
        note = shift_up(note)
        diff += 1
    return diff


class CompositeObject(object):
    def _keys(self):
        raise NotImplementedError

    def __eq__(self, other: "CompositeObject") -> bool:
        try:
            return self._keys() == other._keys()
        except AttributeError:
            return False

    def __hash__(self) -> Hashable:
        return hash(self._keys())
