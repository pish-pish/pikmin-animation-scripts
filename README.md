Python scripts for converting between, and manipulating both Pikmin 1 and Pikmin 2 animation formats.
Custom scripts can be made, and there is an example file found in `gc_anim_tool/scripts`.

*Requires Python 3.11.6+*

Report bugs either here on the repository (preferred) or to `mrpishpish` on discord.

Below is information on each of the python files with arguments enabled. Each argument can also be viewed by using `--help` on either of the files.
Note that there are some basic batch files already available. Several of them are related to the .boi cutscene format for 1^2, and thus are not tremendously useful unless you need raw animation data. 


# conversions.py
- `-i` / `--input` ***Optional***: Input file path for ANM bundles only. For BCX animations, `input` folder will be used.
- `-o` / `--output` ***Optional***: Output path for ANM bundles only. For BCX animations, `output` folder will be used.
- `-s` / `--scale` ***Optional***: After conversion, scale animations by a provided scale value.
    - USAGE: `--scale <scale_value>`
- `--convert_to_bcx` ***Optional***: Convert dca/dck from ANM to bca/bck. Optionally, provide an angle to clamp rotations between `-angle` to `angle`
    - USAGE: `--convert <angle>`
- `--convert_to_dcx` ***Optional***: Convert bca/bck to dca/dck and store in `output`. 
    - Note: This tool does not currently support repacking ANM bundles. Please consider using <https://github.com/Minty-Meeo/piki-tools>.


# cutscene.py
- `-t` / `--target_bmd` ***Required***: Path of reference BMD model to store root translation and/or convert bone order to.
- `-o` / `--original_bmd` ***Optional***: Path of BMD model to have bone order converted.
- `-ic` / `--prep_cutscene` ***Optional***: With this argument, root bone translations will be removed from the animation and exported as an animation entry for .boi cutscene format. The argument by itself will export the pure keyframes, without any trimming.
    - USAGE: `--prep_cutscene clean <threshold>`
- `-r` / `--relative` ***Optional***: Using this argument will perform all translations relative to (0, 0, 0)
- `-s` / `--scale` ***Optional***: Scales animations by a provided scale value.
    - USAGE: `--scale <scale_value>`
