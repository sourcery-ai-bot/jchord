import itertools
from collections import namedtuple
from typing import Hashable, List, Set

from jchord.knowledge import MAJOR_SCALE_OFFSETS, CHROMATIC, ENHARMONIC


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

    def __iter__(self):
        self.__i = 0
        return self

    def __next__(self):
        self.__i += 1
        try:
            return self._keys()[self.__i - 1]
        except IndexError:
            del self.__i
            raise StopIteration

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__, ", ".join(repr(key) for key in self._keys())
        )


class Note(CompositeObject):
    def __init__(self, name, octave):
        self.name = name
        self.octave = octave

    def _keys(self):
        return (self.name, self.octave)

    def __eq__(self, other):
        try:
            other_name = other.name
            other_octave = other.octave
        except AttributeError:
            try:
                if len(other) != 2:
                    return False
            except TypeError:
                return False

            other_name = other[0]
            other_octave = other[1]
        if self.octave != other_octave:
            return False
        if self.name == other_name:
            return True
        for sharp, flat in ENHARMONIC:
            if self.name == sharp:
                return other_name == flat
            elif self.name == flat:
                return other_name == sharp
        return False


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


def semitone_to_degree_options(semitone: int, max_accidentals: int = 1) -> List[str]:
    degrees = MAJOR_SCALE_OFFSETS.copy()
    degrees.update(
        {degree + 7: semitone + 12 for degree, semitone in MAJOR_SCALE_OFFSETS.items()}
    )

    if semitone < 0 or semitone >= 24:
        return []

    options_with_priority = []

    for cand_degree, cand_semitone in degrees.items():
        for n_accidentals in range(max_accidentals + 1):
            if semitone == cand_semitone - n_accidentals:
                options_with_priority.append(
                    ("{}{}".format("b" * n_accidentals, cand_degree), n_accidentals)
                )
            if semitone == cand_semitone + n_accidentals:
                options_with_priority.append(
                    (
                        "{}{}".format("#" * n_accidentals, cand_degree),
                        n_accidentals + 0.5,
                    )
                )

    sorted_options = [
        option
        for option, priority in sorted(
            options_with_priority, key=lambda opt_pri: opt_pri[1]
        )
    ]
    sorted_options_no_duplicates = []
    for option in sorted_options:
        if sorted_options_no_duplicates and sorted_options_no_duplicates[-1] == option:
            continue
        sorted_options_no_duplicates.append(option)
    return sorted_options_no_duplicates


def _shift_up(note: Note) -> Note:
    name, octave = note
    for i, other in enumerate(CHROMATIC):
        if name == other:
            if i == len(CHROMATIC) - 1:
                return Note(name=CHROMATIC[0], octave=octave + 1)
            else:
                return Note(name=CHROMATIC[i + 1], octave=octave)


def _shift_down(note: Note) -> Note:
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
            note = _shift_up(note)
    else:
        for _ in itertools.repeat(None, -shift):
            note = _shift_down(note)
    return note


def transpose_degree(note: Note, shift: str) -> Note:
    return transpose(note, degree_to_semitone(shift))


def note_diff(name_low: str, name_high: str) -> int:
    diff = 0
    note = Note(name_low, 0)
    while note.name != name_high:
        note = _shift_up(note)
        diff += 1
    return diff


def note_to_pitch(note: Note) -> float:
    from jchord import midi

    return midi.midi_to_pitch(midi.note_to_midi(note))
