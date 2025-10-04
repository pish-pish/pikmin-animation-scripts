import math
import binary
from general_animation import Keyframe, JointTrack
from dataclasses import dataclass, field
from io import BufferedIOBase
from pathlib import Path


@dataclass
class J3DDataHeader:
    signature: str = ""
    size: int = 0
    _section_start: int = field(init=False)
    _size_offset: int = field(init=False)

    @classmethod
    def from_file(cls, signature: str, f: BufferedIOBase):
        kind = f.read(len(signature)).decode()
        assert kind == signature

        size = binary.read_u32(f)

        return cls(kind, size)

    def write(self, f: BufferedIOBase):
        self._section_start = f.tell()
        f.write(self.signature.encode())
        self._size_offset = f.tell()
        binary.write_u32(f, self.size)

    def write_size(self, f: BufferedIOBase):
        self.size = f.tell()
        f.seek(self._size_offset)
        binary.write_u32(f, self.size - self._section_start)


class LoopMode:
    """Possible J3D animation loop modes."""

    ONCE = 0
    ONCE_RESET = 1
    LOOP = 2
    MIRRORED_ONCE = 3
    MIRRORED_LOOP = 4


@dataclass
class J3DSkeletonAnimation:
    """Base for J3D skeleton animation formats."""

    @dataclass
    class Header(J3DDataHeader):
        section_count: int = 1

        @classmethod
        def from_file(cls, signature: str, f: BufferedIOBase):
            header = super().from_file(signature, f)

            header.section_count = binary.read_u32(f)
            assert header.section_count == 1

            f.read(16)  # skip svn/svr data and sound section offset

            return header

        def write(self, f: BufferedIOBase):
            super().write(f)
            binary.write_u32(f, self.section_count)
            f.write(b"\xff" * 16)  # padding for svn/svr data and sound section offset

    MAGIC = ""
    SECTION = ""

    name: str
    duration: int
    loop_mode: int
    tracks: list[JointTrack]

    angle_scale: float = 0

    def __post_init__(self):
        self.header = self.Header(self.MAGIC)

        angle_multiplier = self.get_angle_multiplier()
        if angle_multiplier < 0:
            self.angle_scale = 180.0 / 32768.0
            return
        self.angle_scale = float(2**angle_multiplier) * (180.0 / 32768.0)

    def read_channel(
        self, f: BufferedIOBase, channel_data: list[float]
    ) -> list[Keyframe]:
        """Child classes should implement this function. Meant to read scale and translation channels, as in BCA/BCK they are processed as floats."""
        return []

    def read_rotation(
        self, f: BufferedIOBase, channel_data: list[int]
    ) -> list[Keyframe]:
        """Child classes should implement this function. Meant to read the rotation channels, as in BCA/BCK they are processed as shorts with an angle scale modifier."""
        return []

    def write_channel(
        self, f: BufferedIOBase, key_data: list[Keyframe], channel_data: list[float]
    ):
        """Child classes should implement this function. Meant to write scale and translation channels, as in BCA/BCK they are processed as floats."""
        return []

    def write_rotation(
        self, f: BufferedIOBase, key_data: list[Keyframe], channel_data: list[int]
    ):
        """Child classes should implement this function. Meant to write the rotation channels, as in BCA/BCK they are processed as shorts with an angle scale modifier."""
        return []

    def get_angle_multiplier(self) -> int: ...

    def _read_data_section(self, f: BufferedIOBase):
        J3DDataHeader.from_file(self.SECTION, f)

        self.loop_mode = binary.read_u8(f)

        angle_multiplier = binary.read_s8(f)
        if angle_multiplier == -1:
            angle_multiplier = 0
        self.angle_scale = float(2**angle_multiplier) * (180.0 / 32768.0)
        print(f"Read angle_multiplier: {angle_multiplier}")

        self.duration = binary.read_u16(f)

        track_count = binary.read_u16(f)
        scale_count = binary.read_u16(f)
        rotation_count = binary.read_u16(f)
        translation_count = binary.read_u16(f)

        print(f"Read scale_count: {scale_count}")
        print(f"Read rotation_count: {rotation_count}")
        print(f"Read translation_count: {translation_count}")

        # 32 is added to each offset to skip the padding data between each table
        tracks_offset = binary.read_u32(f) + 32
        scales_offset = binary.read_u32(f) + 32
        rotations_offset = binary.read_u32(f) + 32
        translations_offset = binary.read_u32(f) + 32

        scale_data = binary.read_f32_table(f, scales_offset, scale_count)
        rotation_data = binary.read_s16_table(f, rotations_offset, rotation_count)
        translation_data = binary.read_f32_table(
            f, translations_offset, translation_count
        )

        # populate tracks with Keyframe channels, per axis
        f.seek(tracks_offset)
        scale_temp, rotation_temp, translation_temp = (0, 0, 0)
        for _ in range(track_count):
            track = JointTrack()
            for axis in "XYZ":
                track.scale_keys[axis] = self.read_channel(f, scale_data)
                scale_temp += len(track.scale_keys[axis])
                track.rotation_keys[axis] = self.read_rotation(f, rotation_data)
                rotation_temp += len(track.rotation_keys[axis])
                track.translation_keys[axis] = self.read_channel(f, translation_data)
                translation_temp += len(track.translation_keys[axis])
            self.tracks.append(track)
        print(f"Actual scale_count: {scale_temp}")
        print(f"Actual rotation_count: {rotation_temp}")
        print(f"Actual translation_count: {translation_temp}")

    def _write_data_section(self, f: BufferedIOBase):
        section_start = f.tell()
        header = J3DDataHeader(self.SECTION)
        header.write(f)

        binary.write_u8(f, self.loop_mode)
        binary.write_s8(f, self.get_angle_multiplier())
        print(f"Written angle_multiplier: {self.get_angle_multiplier()}")
        binary.write_u16(f, self.duration)

        tracks_count = len(self.tracks)
        binary.write_u16(f, tracks_count)

        count_offset_start = f.tell()
        # placeholders for SRT counts
        for _ in range(3):
            binary.write_u16(f, 0)

        data_offset_start = f.tell()
        # placeholder u32s for data offsets
        for _ in range(4):
            binary.write_u32(f, 0)

        binary.write_padding(f, 32)
        tracks_offset = f.tell()

        scale_data = list[float]()
        rotation_data = list[int]()
        translation_data = list[float]()

        for track in self.tracks:
            for axis in "XYZ":
                self.write_channel(f, track.scale_keys[axis], scale_data)
                self.write_rotation(f, track.rotation_keys[axis], rotation_data)
                self.write_channel(f, track.translation_keys[axis], translation_data)

        binary.write_padding(f, 32)
        scales_offset = f.tell()
        binary.write_f32_table(f, scale_data)

        binary.write_padding(f, 32)
        rotations_offset = f.tell()
        binary.write_s16_table(f, rotation_data)

        binary.write_padding(f, 32)
        translations_offset = f.tell()
        binary.write_f32_table(f, translation_data)

        binary.write_padding(f, 32)

        section_end = f.tell()
        header.write_size(f)

        f.seek(count_offset_start)
        binary.write_u16(f, len(scale_data))
        binary.write_u16(f, len(rotation_data))
        binary.write_u16(f, len(translation_data))

        print(f"Written scale_data: {len(scale_data)}")
        print(f"Written rotation_data: {len(rotation_data)}")
        print(f"Written translation_data: {len(translation_data)}")

        f.seek(data_offset_start)
        binary.write_u32(f, tracks_offset - section_start)
        binary.write_u32(f, scales_offset - section_start)
        binary.write_u32(f, rotations_offset - section_start)
        binary.write_u32(f, translations_offset - section_start)

        f.seek(section_end)

    def write(self, filepath: Path | str):
        extension = self.MAGIC.split("1")[1]
        path = Path(f"{filepath}/{self.name}.{extension}")
        header = self.Header(self.MAGIC)
        with open(path, "wb") as f:
            header.write(f)
            self._write_data_section(f)
            header.write_size(f)

    @classmethod
    def from_file(cls, filepath: str | Path):
        path = Path(filepath)
        name = path.stem

        anim = cls(name, 0, 0, [])

        with open(path, "rb") as f:
            cls.Header.from_file(cls.MAGIC, f)
            anim._read_data_section(f)

        return anim
