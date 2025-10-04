import math
import binary
import general_animation
from pathlib import PurePath
from dataclasses import dataclass
from mod_animation import MODSkeletonAnimation, Keyframe
from io import BufferedIOBase


@dataclass
class DCA(MODSkeletonAnimation):
    def convert_rotations(self):
        for joint in self.joints:
            for axis in "XYZ":
                rotations = joint.rotation_keys[axis]
                for key in rotations:
                    key.value = math.atan2(math.sin(key.value), math.cos(key.value))
                    key.value = math.degrees(key.value)

    def write_to_path(self, filepath: str | PurePath):
        extension = ".dca"

        if extension in self.name:
            extension = ""

        path = PurePath(f"{filepath}/{self.name}{extension}")
        with open(path, "wb") as f:
            self.write(f)

    @staticmethod
    def read_keyframes(
        f: BufferedIOBase, channel_values: list[float]
    ) -> list[Keyframe]:
        keyframe_count = binary.read_u32(f)
        data_index = binary.read_u32(f)

        if keyframe_count == 1:
            # return an identity keyframe, will always have a time value of zero
            return [Keyframe(0, channel_values[data_index])]

        key_data = list[Keyframe]()
        for i in range(keyframe_count):
            key_data.append(Keyframe(i, channel_values[data_index + i]))

        return key_data

    def write_keyframes(
        self, f: BufferedIOBase, key_data: list[Keyframe], channel_values: list[float]
    ):
        channel_sequence = [key.value for key in key_data]

        data_index = general_animation.find_sequence(channel_values, channel_sequence)

        binary.write_u32(f, len(key_data))
        binary.write_u32(f, data_index)
