# conversions.py
- `-i` / `--input` ***Required***: Input file path.
- `-o` / `--output` ***Optional***: Output path.
- `-s` / `--scale` ***Optional***: After conversion, scale animations by a provided scale value.
    - USAGE: `--scale <scale_value>`
- `-c` / `--convert` ***Optional***: Convert dca/dck from ANM to bca/bck. Optionally, provide an angle to clamp rotations between `-angle` to `angle`
    - USAGE: `--convert <angle>`

# cutscene.py
- `-t` / `--target_bmd` ***Required***: Path of reference BMD model to store root translation and/or convert bone order to.
- `-o` / `--original_bmd` ***Optional***: Path of BMD model to have bone order converted.
- `-ic` / `--prep_cutscene` ***Optional***: With this argument, root bone translations will be removed from the animation and exported as an animation entry for .boi cutscene format. The argument by itself will export the pure keyframes, without any trimming.
    - USAGE: `--prep_cutscene clean <threshold>`
- `-r` / `--relative` ***Optional***: Using this argument will perform all translations relative to (0, 0, 0)
- `-s` / `--scale` ***Optional***: Scales animations by a provided scale value.
    - USAGE: `--scale <scale_value>`
