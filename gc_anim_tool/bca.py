import binary
import general_animation
import math
from j3d_animation import J3DSkeletonAnimation, Keyframe
from dataclasses import dataclass
from io import BufferedIOBase


@dataclass
class BCA(J3DSkeletonAnimation):
    """J3D skeleton animation with full frame tracks. No interpolation is done here."""

    MAGIC = "J3D1bca1"
    SECTION = "ANF1"

    def convert_rotations(self):
        for joint in self.tracks:
            for axis in "XYZ":
                rotations = joint.rotation_keys[axis]
                for key in rotations:
                    key.value = math.radians(key.value)

    def get_angle_multiplier(self) -> int:
        return -1

    def read_channel(
        self, f: BufferedIOBase, channel_data: list[float]
    ) -> list[Keyframe]:
        keyframe_count = binary.read_u16(f)
        data_index = binary.read_u16(f)  # index to value in data table

        if keyframe_count == 1:
            # return an identity keyframe, will always have a time value of zero
            return [Keyframe(0, channel_data[data_index])]

        key_data = list[Keyframe]()
        for i in range(keyframe_count):
            key_data.append(Keyframe(i, channel_data[data_index + i]))

        return key_data

    def read_rotation(
        self, f: BufferedIOBase, channel_data: list[int]
    ) -> list[Keyframe]:
        keyframe_count = binary.read_u16(f)
        data_index = binary.read_u16(f)  # index to value in data table

        if keyframe_count == 1:
            # return an identity keyframe, will always have a time value of zero
            return [Keyframe(0, channel_data[data_index] * self.angle_scale)]

        key_data = list[Keyframe]()
        for i in range(keyframe_count):
            key_data.append(
                Keyframe(i, channel_data[data_index + i] * self.angle_scale)
            )

        return key_data

    def write_channel(
        self, f: BufferedIOBase, key_data: list[Keyframe], channel_data: list[float]
    ):
        channel_sequence = [key.value for key in key_data]

        data_index = general_animation.find_sequence(channel_data, channel_sequence)

        binary.write_u16(f, len(key_data))
        binary.write_u16(f, data_index)

    def write_rotation(
        self, f: BufferedIOBase, key_data: list[Keyframe], channel_data: list[int]
    ):
        channel_sequence = [int(key.value / self.angle_scale) for key in key_data]

        data_index = general_animation.find_sequence(channel_data, channel_sequence)

        binary.write_u16(f, len(key_data))
        binary.write_u16(f, data_index)
