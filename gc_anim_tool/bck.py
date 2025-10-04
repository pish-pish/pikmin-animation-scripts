import binary
import general_animation
import math
from general_animation import TangentMode
from j3d_animation import J3DSkeletonAnimation, Keyframe
from dataclasses import dataclass
from io import BufferedIOBase
from itertools import chain


@dataclass
class BCK(J3DSkeletonAnimation):
    """J3D skeleton animation with interpolated keyframe tracks."""

    MAGIC = "J3D1bck1"
    SECTION = "ANK1"

    def get_angle_multiplier(self) -> int:
        max_angle = 0.0
        for track in self.tracks:
            for axis in "XYZ":
                values = [abs(key.value) for key in track.rotation_keys[axis]]
                max_angle = max(max_angle, max(values))

        max_angle = math.ceil(max_angle)
        if max_angle < 180:
            return 0

        return int(max_angle / 180)

    def read_channel(
        self, f: BufferedIOBase, channel_data: list[float]
    ) -> list[Keyframe]:
        keyframe_count = binary.read_u16(f)
        data_index = binary.read_u16(f)
        tangent_mode = binary.read_u16(f)

        if keyframe_count == 1:
            return [Keyframe(0, channel_data[data_index])]

        key_data = list[Keyframe]()
        for i in range(keyframe_count):
            current_index = data_index

            if tangent_mode == TangentMode.SYMMETRIC:
                current_index += 3 * i
                out_tangent = None
            else:
                current_index += 4 * i
                out_tangent = channel_data[current_index + 3]

            key_data.append(
                Keyframe(
                    channel_data[current_index],
                    channel_data[current_index + 1],
                    channel_data[current_index + 2],
                    out_tangent,
                )
            )

        return key_data

    def read_rotation(
        self, f: BufferedIOBase, channel_data: list[int]
    ) -> list[Keyframe]:
        keyframe_count = binary.read_u16(f)
        data_index = binary.read_u16(f)
        tangent_mode = binary.read_u16(f)

        if keyframe_count == 1:
            return [Keyframe(0, channel_data[data_index] * self.angle_scale)]

        key_data = list[Keyframe]()
        for i in range(keyframe_count):
            current_index = data_index

            if tangent_mode == TangentMode.SYMMETRIC:
                current_index += 3 * i
                out_tangent = None
            else:
                current_index += 4 * i
                out_tangent = channel_data[current_index + 3] * self.angle_scale

            key_data.append(
                Keyframe(
                    channel_data[current_index],
                    channel_data[current_index + 1] * self.angle_scale,
                    channel_data[current_index + 2] * self.angle_scale,
                    out_tangent,
                )
            )

        return key_data

    def write_channel(
        self, f: BufferedIOBase, key_data: list[Keyframe], channel_data: list[float]
    ):
        tangent_type = TangentMode.SYMMETRIC
        if len(key_data) == 1:
            channel_sequence = [key.value for key in key_data]
        else:
            channel_sequence = list(
                chain.from_iterable([key.to_f32_list() for key in key_data])
            )
            for key in key_data:
                if key.out_tangent != None and key.in_tangent != key.out_tangent:
                    tangent_type = TangentMode.PIECEWISE
                    break

        data_index = general_animation.find_sequence(channel_data, channel_sequence)

        binary.write_u16(f, len(key_data))
        binary.write_u16(f, data_index)
        binary.write_u16(f, tangent_type)

    def write_rotation(
        self, f: BufferedIOBase, key_data: list[Keyframe], channel_data: list[int]
    ):
        tangent_type = TangentMode.SYMMETRIC
        if len(key_data) == 1:
            channel_sequence = [int(key.value / self.angle_scale) for key in key_data]
        else:
            channel_sequence = list(
                chain.from_iterable(
                    [key.to_s16_list(self.angle_scale) for key in key_data]
                )
            )
            for key in key_data:
                if key.out_tangent != None and key.in_tangent != key.out_tangent:
                    tangent_type = TangentMode.PIECEWISE
                    break

        data_index = general_animation.find_sequence(channel_data, channel_sequence)

        binary.write_u16(f, len(key_data))
        binary.write_u16(f, data_index)
        binary.write_u16(f, tangent_type)
