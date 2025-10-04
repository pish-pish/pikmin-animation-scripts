import math
import binary
from dataclasses import dataclass, field
from io import BufferedIOBase, BytesIO
from pathlib import Path
from general_animation import Keyframe, JointTrack


@dataclass
class Joint(JointTrack):
    joint_index: int = 0
    parent_index: int = 0


@dataclass
class MODSkeletonAnimation:
    name: str
    duration: int
    joints: list[Joint]

    filesize: int = field(init=False)

    def convert_rotations(self): ...

    def sort_joints(self):
        def get_joint_index(joint: Joint):
            return joint.joint_index

        self.joints.sort(key=get_joint_index)

    @staticmethod
    def read_keyframes(
        f: BufferedIOBase, channel_values: list[float]
    ) -> list[Keyframe]: ...

    def write_keyframes(
        self,
        f: BufferedIOBase,
        channel_keys: list[Keyframe],
        channel_values: list[float],
    ): ...

    def write(self, f: BufferedIOBase):
        binary.write_u32(f, len(self.joints))
        print(f"joint_count: {len(self.joints)}")
        binary.write_u32(f, self.duration)
        print(f"duration: {self.duration}")

        scale_data = list[float]()
        rotation_data = list[float]()
        translation_data = list[float]()

        joint_buffer = BytesIO()
        for joint in self.joints:
            binary.write_u32(joint_buffer, joint.joint_index)
            binary.write_u32(joint_buffer, joint.parent_index)

            for axis in "XYZ":
                self.write_keyframes(joint_buffer, joint.scale_keys[axis], scale_data)
            for axis in "XYZ":
                self.write_keyframes(
                    joint_buffer, joint.rotation_keys[axis], rotation_data
                )
            for axis in "XYZ":
                self.write_keyframes(
                    joint_buffer, joint.translation_keys[axis], translation_data
                )

        binary.write_u32(f, len(scale_data))  # scales_count
        print(f"scales_count: {len(scale_data)}")
        binary.write_f32_table(f, scale_data)

        binary.write_u32(f, len(rotation_data))  # rotations_count
        print(f"rotations_count: {len(rotation_data)}")
        binary.write_f32_table(f, rotation_data)

        binary.write_u32(f, len(translation_data))  # translations_count
        print(f"translations_count: {len(translation_data)}")
        binary.write_f32_table(f, translation_data)

        f.write(joint_buffer.getvalue())

        self.filesize = f.tell()

    def write_to_path(self, filepath: str | Path): ...

    @classmethod
    def from_file(cls, f: BufferedIOBase):
        joint_count = binary.read_u32(f)
        duration = binary.read_u32(f)

        scales_count = binary.read_u32(f)
        scale_values = binary.read_f32_table(f, f.tell(), scales_count)

        rotations_count = binary.read_u32(f)
        rotation_values = binary.read_f32_table(f, f.tell(), rotations_count)

        translations_count = binary.read_u32(f)
        translation_values = binary.read_f32_table(f, f.tell(), translations_count)

        joints = list[Joint]()
        for _ in range(joint_count):
            joint_index = binary.read_u32(f)
            parent_index = binary.read_u32(f)

            joint = Joint(joint_index, parent_index)
            for axis in "XYZ":
                joint.scale_keys[axis] = cls.read_keyframes(f, scale_values)
            for axis in "XYZ":
                joint.rotation_keys[axis] = cls.read_keyframes(f, rotation_values)
            for axis in "XYZ":
                joint.translation_keys[axis] = cls.read_keyframes(f, translation_values)

            joints.append(joint)

        return cls("", duration, joints)

    @classmethod
    def from_filepath(cls, filepath: str | Path):
        path = Path(filepath)
        name = path.stem
        with open(path, "rb") as f:
            anim = cls.from_file(f)
            anim.name = name
        return anim
