import math
from pathlib import Path
from typing import Optional
from argparse import ArgumentParser
from j3d_animation import LoopMode, J3DSkeletonAnimation
from mod_animation import MODSkeletonAnimation, Joint
from general_animation import scale_animation
from glob import glob
from cutscene import sort_file
from anm import ANM
from dca import DCA
from dck import DCK
from bca import BCA
from bck import BCK


def convert_anm_bundle(anm: ANM, clamp: Optional[float] = None) -> list[BCA | BCK]:
    out = []
    for anim in anm.animations:
        if isinstance(anim, DCA):
            out.append(dca_to_bca(anim))
        elif isinstance(anim, DCK):
            out.append(dck_to_bck(anim, clamp))

    return out


def dca_to_bca(dca: DCA) -> BCA:
    name = Path(dca.name).stem
    dca.convert_rotations()
    dca.sort_joints()
    return BCA(name, dca.duration, LoopMode.LOOP, dca.joints)  # type: ignore


def dck_to_bck(dck: DCK, clamp: Optional[float] = None) -> BCK:
    name = Path(dck.name).stem
    dck.convert_rotations(clamp)
    dck.sort_joints()
    dck.fix_tangents()
    return BCK(name, dck.duration, LoopMode.LOOP, dck.joints)  # type: ignore

def convert_tracks_to_joints(anim: J3DSkeletonAnimation) -> list[Joint]:
    joints = list[Joint]()
    for i, track in enumerate(anim.tracks):
        joint = Joint(i, 0)
        joint.translation_keys = track.translation_keys
        joint.rotation_keys = track.rotation_keys
        joint.scale_keys = track.scale_keys
        joints.append(joint)

    return joints

def bca_to_dca(bca: BCA) -> DCA:
    bca.convert_rotations()
    joints = convert_tracks_to_joints(bca)
    return DCA(bca.name, bca.duration, joints)


def bck_to_dck(bck: BCK) -> DCK:
    bck.convert_rotations()
    bck.fix_tangents()
    joints = convert_tracks_to_joints(bck)
    return DCK(bck.name, bck.duration, joints)


def write_rotations_to_file(
    anim: J3DSkeletonAnimation | MODSkeletonAnimation, filepath: str | Path
):
    extension = ""
    tracks = []
    if isinstance(anim, BCK):
        extension = "bck"
        tracks = anim.tracks
    elif isinstance(anim, DCK):
        extension = "dck"
        tracks = anim.joints

    path = Path(rf"{filepath}/{anim.name}_rot_{extension}.txt")
    with open(path, "w") as f:
        f.write(anim.name)
        for i, track in enumerate(tracks):
            f.write(f"Joint: {i}\n")
            for axis in "XYZ":
                f.write(axis + "\n")
                for key in track.rotation_keys[axis]:
                    if isinstance(anim, DCK):
                        f.write(str(math.degrees(key.value)) + "\n")
                        continue
                    elif isinstance(anim, BCK):
                        value = int(key.value / anim.angle_scale)
                        f.write(str(value * anim.angle_scale) + "\n")
            f.write("\n")


INPUT = Path("./input/")
OUTPUT = Path("./output/")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="<Optional> Input file path.")
    parser.add_argument("-o", "--output", type=str, help="<Optional> Output path.")
    parser.add_argument(
        "-s",
        "--scale",
        default=1.0,
        type=float,
        help="<Optional> After conversion, scale animations by a provided scale value.",
    )
    parser.add_argument(
        "--convert_to_bcx",
        nargs="*",
        help="<Optional> Convert dca/dck from ANM to bca/bck. \
              Optionally, provide an angle to clamp rotations between <-angle> to <angle>",
    )
    parser.add_argument(
        "--convert_to_dcx",
        action="store_true",
        help="<Optional> Using this argument will convert bck/bca anims in the `input` folder to dca/dck and pack them into an ANM bundle.",
    )

    args = parser.parse_args()

    if args.input != None and args.input != "":
        anm = ANM.from_filepath(rf"{args.input}")

        output = Path(rf"{args.input}").parent
        if args.output != None and args.output != "":
            output = Path(rf"{args.output}")
            output.mkdir(parents=True, exist_ok=True)

    if args.convert_to_bcx == [] or args.convert_to_bcx:
        clamp = None
        if len(args.convert_to_bcx) > 0:
            clamp = args.convert_to_bcx[0]
        anims = convert_anm_bundle(anm, clamp)
        for anim in anims:
            scale_animation(anim.tracks, args.scale)
            anim.write(output)
    elif args.convert_to_dcx:
        for type in (".bca", ".bck"):
            paths = glob(rf"{INPUT}/*{type}")
            for path in paths:
                anim = sort_file(Path(path))
                if isinstance(anim, BCA):
                    output_anim = bca_to_dca(anim)
                    output_anim.write_to_path(OUTPUT)
                elif isinstance(anim, BCK):
                    output_anim = bck_to_dck(anim)
                    output_anim.write_to_path(OUTPUT)
    else:
        for anim in anm.animations:
            anim.write_to_path(output)
