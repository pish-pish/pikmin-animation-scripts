import math
from pathlib import Path
from typing import Optional
from argparse import ArgumentParser
from j3d_animation import LoopMode, J3DSkeletonAnimation
from mod_animation import MODSkeletonAnimation
from general_animation import scale_animation
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


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-i", "--input", type=str, required=True, help="<Required> Input file path."
    )
    parser.add_argument("-o", "--output", type=str, help="<Optional> Output path.")
    parser.add_argument(
        "-s",
        "--scale",
        default=1.0,
        type=float,
        help="<Optional> After conversion, scale animations by a provided scale value.",
    )
    parser.add_argument(
        "-c",
        "--convert",
        nargs="*",
        help="<Optional> Convert dca/dck from ANM to bca/bck. \
              Optionally, provide an angle to clamp rotations between <-angle> to <angle>",
    )

    args = parser.parse_args()

    anm = ANM.from_filepath(rf"{args.input}")

    output = Path(rf"{args.input}").parent
    if args.output != None and args.output != "":
        output = Path(rf"{args.output}")
        output.mkdir(parents=True, exist_ok=True)

    if args.convert == [] or args.convert:
        clamp = None
        if len(args.convert) > 0:
            clamp = args.convert[0]
        anims = convert_anm_bundle(anm, clamp)
        for anim in anims:
            scale_animation(anim.tracks, args.scale)
            anim.write(output)
    else:
        for anim in anm.animations:
            anim.write_to_path(output)
