from dataclasses import dataclass, field
from typing import Optional


def find_sequence(in_list: list, seq: list) -> int:
    """Adapted from J3D Animation Editor by Tarsa, this function
    will find a start index to a sequence of data within a larger list,
    if the sequence of data is not unique to the larger list.

    Args:
        in_list (list): list to find a sequence within
        seq (list): sequence of data to find

    Returns:
        int: Index where `seq` starts inside `in_list`
    """
    matchup = 0
    start = -1

    started = False

    for i, val in enumerate(in_list):
        if val != seq[matchup]:
            matchup = 0
            start = -1
            started = False
            continue

        if not started:
            start = i
            started = True

        matchup += 1
        if matchup == len(seq):
            return start

    start = len(in_list)
    in_list.extend(seq)

    return start


class TangentMode:
    """Possible keyframe tangent modes."""

    SYMMETRIC = 0
    PIECEWISE = 1


@dataclass
class Keyframe:
    """Keyframe with optional tangent values."""

    frame: float
    value: float
    in_tangent: Optional[float] = None
    out_tangent: Optional[float] = None

    def to_f32_list(self) -> list[float]:
        out = []

        out.append(self.frame)
        out.append(self.value)

        if self.in_tangent != None:
            out.append(self.in_tangent)
        if self.out_tangent != None and self.out_tangent != self.in_tangent:
            out.append(self.out_tangent)

        return out

    def to_s16_list(self, angle_scale: float) -> list[int]:
        """Intended for rotation keyframes, as they are processed as integers and use an angle multiplier"""
        out = []

        out.append(int(self.frame))
        out.append(int(self.value / angle_scale))

        if self.in_tangent != None:
            out.append(int(self.in_tangent / angle_scale))

        if self.out_tangent != None and self.out_tangent != self.in_tangent:
            out.append(int(self.out_tangent / angle_scale))

        return out


@dataclass
class JointTrack:
    """SRT animation track representing a joint."""

    scale_keys: dict[str, list[Keyframe]] = field(
        init=False, default_factory=lambda: {"X": [], "Y": [], "Z": []}
    )
    rotation_keys: dict[str, list[Keyframe]] = field(
        init=False, default_factory=lambda: {"X": [], "Y": [], "Z": []}
    )
    translation_keys: dict[str, list[Keyframe]] = field(
        init=False, default_factory=lambda: {"X": [], "Y": [], "Z": []}
    )


def scale_animation(tracks: list[JointTrack], scale: float):
    for track in tracks:
        for axis in "XYZ":
            for keyframe in track.translation_keys[axis]:
                keyframe.value *= scale
