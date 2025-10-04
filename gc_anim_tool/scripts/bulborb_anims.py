import sys

sys.path.append("./gc_anim_tool")
from anm import ANM
from conversions import convert_anm_bundle, scale_animation
from cutscene import get_bones_from_bmd, get_bone_transforms
from bca import BCA


def fix_skeleton(anm_file, new_bmd, old_bmd):
    new_bone_transforms = get_bone_transforms(f"./input/{new_bmd}")
    new_bone_names = get_bones_from_bmd(f"./input/{new_bmd}")

    og_bone_names = get_bones_from_bmd(f"./input/{old_bmd}")

    anims = convert_anm_bundle(ANM.from_filepath(f"./input/{anm_file}"))

    for anim in anims:
        names_copy = og_bone_names.copy()

        scale_animation(anim.tracks, 3.0)
        for i in range(5):
            leaf1_index = names_copy.index(f"kamu{i+1}_leaf1")
            names_copy.pop(leaf1_index)
            anim.tracks.pop(leaf1_index)

            leaf2_index = names_copy.index(f"kamu{i+1}_leaf2")
            names_copy.pop(leaf2_index)
            anim.tracks.pop(leaf2_index)

            kamu_index = new_bone_names.index(f"kamu{i+1}")
            leaf3_index = names_copy.index(f"kamu{i+1}")

            anim.tracks[leaf3_index].translation_keys = new_bone_transforms[
                kamu_index
            ].translation_keys

            anim.tracks[leaf3_index].rotation_keys = new_bone_transforms[
                kamu_index
            ].rotation_keys

            if isinstance(anim, BCA):
                for axis in "XYZ":
                    for keyframe in anim.tracks[leaf3_index].rotation_keys[axis]:
                        clamp = 180
                        keyframe.value %= clamp * 2
                        keyframe.value = (keyframe.value % (clamp * 2)) % (clamp * 2)
                        if keyframe.value > clamp:
                            keyframe.value -= clamp * 2

            anim.tracks[leaf3_index].scale_keys = new_bone_transforms[
                kamu_index
            ].scale_keys

        anim.write("./output/")


def convert_bulborb():
    fix_skeleton("swallow.anm", "bulborb.bmd", "bulborb_old.bmd")


def convert_bulbear():
    fix_skeleton("swallob.anm", "bulbear.bmd", "bulbear_old.bmd")


convert_bulbear()
