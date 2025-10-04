import sys

sys.path.append("./gc_anim_tool")
from conversions import dck_to_bck
from bck import BCK
from dck import DCK
from j3d_animation import LoopMode, Keyframe
from glob import glob
from pathlib import Path


def convert_good_ending():
    original = dck_to_bck(DCK.from_filepath("./input/dm76_ufo.dck"))
    suction = BCK.from_file("./input/suction2.bck")
    for track in suction.tracks:
        for axis in "XYZ":
            track.translation_keys[axis] = track.translation_keys[axis][:1]
            track.rotation_keys[axis] = track.rotation_keys[axis][:1]
            track.scale_keys[axis] = track.scale_keys[axis][:1]

    for i in range(1):
        suction.tracks[i].translation_keys = original.tracks[i].translation_keys
        suction.tracks[i].rotation_keys = original.tracks[i].rotation_keys
        suction.tracks[i].scale_keys = original.tracks[i].scale_keys

    new_bck = BCK(original.name, original.duration, LoopMode.ONCE, suction.tracks)
    new_bck.write("./output/")


def offset_dayend_results():
    def offset_channel(channel: list[Keyframe]) -> list[Keyframe]:
        if len(channel) <= 1:
            return channel

        out = list[Keyframe]()
        for i, key in enumerate(channel):
            if i == 0:
                out.append(key)
                continue

            if key.frame > 180:
                key.frame -= 180
                out.append(key)

        return out

    paths = glob(rf"./input/*.bck")
    for path in paths:
        anim = BCK.from_file(Path(path))
        for track in anim.tracks:
            for axis in "XYZ":
                track.translation_keys[axis] = offset_channel(
                    track.translation_keys[axis]
                )
                track.rotation_keys[axis] = offset_channel(track.rotation_keys[axis])
                track.scale_keys[axis] = offset_channel(track.scale_keys[axis])

            y_offset = abs(track.translation_keys["Y"][0].value)
            for key in track.translation_keys["Y"]:
                if key.frame == 0:
                    continue
                key.value -= y_offset

        new_bck = BCK(anim.name, anim.duration - 180, LoopMode.ONCE, anim.tracks)
        new_bck.write("./output/")


if __name__ == "__main__":
    # convert_good_ending()
    offset_dayend_results()
    pass
