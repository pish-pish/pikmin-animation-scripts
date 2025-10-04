import binary
import math
from io import BufferedIOBase
from argparse import ArgumentParser
from glob import glob
from pathlib import Path
from dataclasses import dataclass, field
from bca import BCA
from bck import BCK
from general_animation import Keyframe, JointTrack, scale_animation
from j3d_animation import J3DSkeletonAnimation


def get_bone_transforms(bmd_file) -> list[JointTrack]:
    """Adapted from J3D Animation Editor by Tarsa"""
    with open(bmd_file, "rb") as f:
        s = f.read()
        a = s.find("JNT1".encode())

        f.seek(a + 0x08)
        bone_count = binary.read_u16(f)
        f.seek(a + 0x0C)
        address = binary.read_u32(f)
        f.seek(address + a)

        tracks = list[JointTrack]()
        for _ in range(bone_count):
            track = JointTrack()
            f.read(4)
            for axis in "XYZ":
                track.scale_keys[axis] = [Keyframe(0, binary.read_f32(f))]

            for axis in "XYZ":
                track.rotation_keys[axis] = [
                    Keyframe(0, binary.read_u16(f) * (180.0 / 32768.0))
                ]

            f.read(2)
            for axis in "XYZ":
                track.translation_keys[axis] = [Keyframe(0, binary.read_f32(f))]

            f.read(28)

            tracks.append(track)

        return tracks


def get_bones_from_bmd(bmd_filepath: str):
    """Adapted from J3D Animation Editor by Tarsa"""

    def stringtable_from_file(f: BufferedIOBase) -> list[str]:
        """Adapted from J3D Animation Editor by Tarsa"""
        strings = list[str]()

        start = f.tell()

        string_count = binary.read_u16(f)
        f.read(2)  # 0xFFFF

        offsets = []
        for _ in range(string_count):
            binary.read_u16(f)
            string_offset = binary.read_u16(f)
            offsets.append(string_offset)

        for offset in offsets:
            f.seek(start + offset)

            # Read 0-terminated string
            string_length = 0
            while f.read(1) != b"\x00":
                string_length += 1

            f.seek(start + offset)

            if string_length == 0:
                strings.append("")
            else:
                strings.append(f.read(string_length).decode("shift-jis"))

        return strings

    strings = list[str]()
    with open(bmd_filepath, "rb") as f:
        s = f.read()
        a = s.find("JNT1".encode())
        f.seek(a + 0x14)
        address = binary.read_u32(f)
        f.seek(address + a)
        strings = stringtable_from_file(f)
        f.close()

    return strings


def align_to_skeleton(
    anim: J3DSkeletonAnimation, input_names: list[str], target_names: list[str]
) -> BCA | BCK:
    skeleton = dict(zip(input_names, anim.tracks))
    skeleton = {name: skeleton[name] for name in target_names if name in skeleton}

    out_anim: J3DSkeletonAnimation
    if isinstance(anim, BCK):
        out_anim = BCK(
            anim.name, anim.duration, anim.loop_mode, list(skeleton.values())
        )
    elif isinstance(anim, BCA):
        out_anim = BCA(
            anim.name, anim.duration, anim.loop_mode, list(skeleton.values())
        )

    return out_anim


def sort_file(filepath: str | Path) -> BCK | BCA:
    with open(filepath, "rb") as f:
        magic = f.read(8).decode()
        f.close()

    if magic == BCA.MAGIC:
        return BCA.from_file(filepath)
    elif magic == BCK.MAGIC:
        return BCK.from_file(filepath)

    raise AssertionError("File is not BCA or BCK")


def clear_root_translation(y_offset: float, anim: J3DSkeletonAnimation):
    for axis in "XYZ":
        anim.tracks[0].translation_keys[axis] = [Keyframe(0, 0)]
    anim.tracks[0].translation_keys["Y"][0].value = y_offset


@dataclass
class AnimationEntry:
    animation: J3DSkeletonAnimation
    y_offset: float = field(default=0.0)
    x_movement_keys: list[Keyframe] = field(default_factory=list[Keyframe])
    y_movement_keys: list[Keyframe] = field(default_factory=list[Keyframe])
    z_movement_keys: list[Keyframe] = field(default_factory=list[Keyframe])

    def __post_init__(self):
        root_translation = self.animation.tracks[0].translation_keys

        self.x_movement_keys = root_translation["X"]

        for key in root_translation["Y"]:
            key.value -= self.y_offset
        self.y_movement_keys = root_translation["Y"]

        self.z_movement_keys = root_translation["Z"]

    # clean bck by removing duplicates
    def get_clean_duplicates(
        self, channel: list[Keyframe], threshold: float
    ) -> list[Keyframe]:
        duplicates = list[Keyframe]()
        for i, current_key in enumerate(channel):
            next_frame = i + 1
            next_key = channel[next_frame % len(channel)]

            # failsafe for null tangent (this happens with animations with 0 movement)
            if isinstance(current_key.in_tangent, float) is False:
                current_key.in_tangent = 0
            if isinstance(next_key.in_tangent, float) is False:
                next_key.in_tangent = 0

            is_value_equal = math.isclose(
                current_key.value, next_key.value, rel_tol=threshold
            )
            is_tangent_equal = math.isclose(current_key.in_tangent, next_key.in_tangent, rel_tol=threshold)  # type: ignore
            if is_value_equal and is_tangent_equal:
                duplicates.append(next_key)

        return [key for key in channel if key not in duplicates[1:-2]]

    # clean bca by taking slope between each point and comparing them with a threshold
    def get_clean_starting_points(
        self, channel: list[Keyframe], threshold: float
    ) -> list[Keyframe]:
        starting_points = list[int]([0])
        for current_frame, current_key in enumerate(channel):
            next_frame = current_frame + 1
            next_key = channel[next_frame % len(channel)]
            # get the current slope between the current frame and next frame
            current_slope = (next_key.value - current_key.value) / (
                next_frame - current_frame
            )

            # get the next slope between the next frame and the frame after
            current_frame = next_frame
            current_key = next_key
            next_frame += 1
            next_key = channel[next_frame % len(channel)]

            next_slope = (next_key.value - current_key.value) / (
                next_frame - current_frame
            )

            if abs(next_slope - current_slope) >= threshold:
                starting_points.append(current_frame)

        return [key for key in channel if key in starting_points]

    def clean_keyframes(self, threshold=0.01):
        if isinstance(self.animation, BCK):
            self.x_movement_keys = self.get_clean_duplicates(
                self.x_movement_keys, threshold
            )
            self.y_movement_keys = self.get_clean_duplicates(
                self.y_movement_keys, threshold
            )
            self.z_movement_keys = self.get_clean_duplicates(
                self.z_movement_keys, threshold
            )
        elif isinstance(self.animation, BCA):
            self.x_movement_keys = self.get_clean_starting_points(
                self.x_movement_keys, threshold
            )
            self.y_movement_keys = self.get_clean_starting_points(
                self.y_movement_keys, threshold
            )
            self.z_movement_keys = self.get_clean_starting_points(
                self.z_movement_keys, threshold
            )

    def __str__(self) -> str:
        x_keys = "\t" + "\n\t".join(
            [
                f"{int(x.frame)}\t{x.value:.6f}\t{x.in_tangent*30.0:.6f}"  # type: ignore
                for x in self.x_movement_keys
            ]
        )

        y_keys = "\t" + "\n\t".join(
            [
                f"{int(y.frame)}\t{y.value:.6f}\t{y.in_tangent*30.0:.6f}"  # type: ignore
                for y in self.y_movement_keys
            ]
        )

        z_keys = "\t" + "\n\t".join(
            [
                f"{int(z.frame)}\t{z.value:.6f}\t{z.in_tangent*30.0:.6f}"  # type: ignore
                for z in self.z_movement_keys
            ]
        )

        entry = [
            f"{len(self.x_movement_keys)}\t\t# x movement keys",
            "{",
            x_keys,
            "}\n",
            f"{len(self.y_movement_keys)}\t\t# y movement keys",
            "{",
            y_keys,
            "}\n",
            f"{len(self.z_movement_keys)}\t\t# z movement keys",
            "{",
            z_keys,
            "}",
        ]
        return "\n".join(entry)


INPUT = Path("./input/")
OUTPUT = Path("./output/")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-t",
        "--target_bmd",
        type=str,
        help="<Optional> Name of reference BMD model to convert bone order to.",
    )
    parser.add_argument(
        "-o",
        "--original_bmd",
        type=str,
        help="<Optional> Name of BMD model to have bone order converted.",
    )
    parser.add_argument(
        "-ic",
        "--prep_cutscene",
        nargs="*",
        help="<Optional> With this argument, root bone translations will be removed from the animation and exported as an animation entry for .boi cutscene format. USAGE: --prep_cutscene clean <threshold>",
    )
    parser.add_argument(
        "-r",
        "--relative",
        action="store_true",
        help="<Optional> Using this argument will perform all translations relative to (0, 0, 0)",
    )
    parser.add_argument(
        "-s",
        "--scale",
        default=1.0,
        type=float,
        help="<Optional> After conversion, scale animations by a provided scale value.",
    )

    args = parser.parse_args()

    input_animations = dict[str, J3DSkeletonAnimation]()
    for type in (".bca", ".bck"):
        paths = glob(rf"{INPUT}/*{type}")
        for path in paths:
            path = Path(path)
            input_animations[path.name] = sort_file(path)

    if args.original_bmd != "":
        names_original = get_bones_from_bmd(args.original_bmd)
        names_target = get_bones_from_bmd(args.target_bmd)

    if args.target_bmd != "":
        rest_pose = get_bone_transforms(args.target_bmd)

    for name, anim in input_animations.items():
        output_anim = anim
        if args.original_bmd != "":
            output_anim = align_to_skeleton(anim, names_original, names_target)

        if args.relative:
            # disclude Y because of offset in cleaned frames and in game shadows
            offset: dict[str, float] = {
                "X": anim.tracks[0].translation_keys["X"][0].value,
                "Z": anim.tracks[0].translation_keys["Z"][0].value,
            }

            for axis in "XZ":
                for frame in anim.tracks[0].translation_keys[axis]:
                    frame.value -= offset[axis]

        if args.prep_cutscene == [] or args.prep_cutscene:
            assert args.target_bmd != "", "`target_bmd` is required for this operation."
            y_offset = rest_pose[0].translation_keys["Y"][0].value
            anim_entry = AnimationEntry(anim, y_offset)
            clear_root_translation(y_offset, anim)

            if "clean" in args.prep_cutscene:
                anim_entry.clean_keyframes(float(args.prep_cutscene[1]))

            anim_name = name.split(".")[0].strip()
            with open(rf"{OUTPUT}/{anim_name}_translations.txt", "w") as f:
                f.write(str(anim_entry))
            print(f"Root transforms exported to {anim_name}_translations.txt")

        scale_animation(output_anim.tracks, args.scale)
        output_anim.write(rf"{OUTPUT}")

        print(f"{name} converted successfully...")

    print("All animations converted successfully!")
