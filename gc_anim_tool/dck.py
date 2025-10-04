import math
import binary
import general_animation
from pathlib import Path
from dataclasses import dataclass
from io import BufferedIOBase
from mod_animation import Keyframe, MODSkeletonAnimation
from itertools import chain
from typing import Optional


@dataclass
class DCK(MODSkeletonAnimation):

    def convert_rotations(self, clamp: Optional[float] = None):
        for joint in self.joints:
            for axis in "XYZ":
                rotations = joint.rotation_keys[axis]
                for key in rotations:
                    key.value = math.degrees(key.value)

                    if clamp == None:
                        continue
                    clamp = int(clamp)
                    key.value %= clamp * 2
                    key.value = (key.value % (clamp * 2)) % (clamp * 2)
                    if key.value > clamp:
                        key.value -= clamp * 2

    def fix_tangents(self):
        def set_channel_tangents(channel: list[Keyframe]):
            for key in channel:
                if key.in_tangent != None:
                    key.in_tangent /= 30.0
                if key.out_tangent != None:
                    key.out_tangent /= 30.0

        for joint in self.joints:
            for axis in "XYZ":
                set_channel_tangents(joint.scale_keys[axis])
                set_channel_tangents(joint.rotation_keys[axis])
                set_channel_tangents(joint.translation_keys[axis])

    def write_to_path(self, filepath: str | Path):
        extension = ".dck"

        if extension in self.name:
            extension = ""

        path = Path(f"{filepath}/{self.name}{extension}")
        with open(path, "wb") as f:
            self.write(f)

    @staticmethod
    def read_keyframes(
        f: BufferedIOBase, channel_values: list[float]
    ) -> list[Keyframe]:
        keyframe_count = binary.read_u32(f)
        data_index = binary.read_u32(f)
        tangent_mode = binary.read_u32(f)

        if keyframe_count == 1:
            return [Keyframe(0, channel_values[data_index])]

        key_data = list[Keyframe]()
        for i in range(keyframe_count):
            current_index = data_index + 3 * i
            key_data.append(
                Keyframe(
                    channel_values[current_index],
                    channel_values[current_index + 1],
                    channel_values[current_index + 2],
                )
            )

        return key_data

    def write_keyframes(
        self, f: BufferedIOBase, key_data: list[Keyframe], channel_values: list[float]
    ):
        if len(key_data) == 1:
            channel_sequence = [key_data[0].value]
        else:
            channel_sequence = list(
                chain.from_iterable([key.to_f32_list() for key in key_data])
            )

        data_index = general_animation.find_sequence(channel_values, channel_sequence)

        binary.write_u32(f, len(key_data))
        binary.write_u32(f, data_index)
        binary.write_u32(f, 0)
