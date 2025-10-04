import binary
from dataclasses import dataclass
from dca import DCA
from dck import DCK
from pathlib import Path


class AnmContentIndicator:
    DCA = 2
    DCK = 3


def get_file_name(file_path):
    file_path_components = file_path.split("/")
    file_name_and_extension = file_path_components[-1].rsplit(".", 1)
    return file_name_and_extension[0]


@dataclass
class ANM:
    animations: list[DCK | DCA]

    def write_to_path(self, filepath: str | Path):
        path = Path(filepath)
        with open(path, "wb") as f:
            binary.write_u32(f, len(self.animations))
            for animation in self.animations:
                if isinstance(animation, DCA):
                    binary.write_u32(f, AnmContentIndicator.DCA)
                else:
                    binary.write_u32(f, AnmContentIndicator.DCK)

                size_offset = f.tell()
                binary.write_u32(f, 0)  # placeholder for size

                binary.write_u32(f, len(animation.name))
                f.write(animation.name.encode())

                animation.write(f)

                f.seek(size_offset)
                binary.write_u32(f, animation.filesize)

    @classmethod
    def from_filepath(cls, filepath: str | Path):
        path = Path(filepath)

        animations = []
        with open(path, "rb") as f:
            animation_count = binary.read_u32(f)
            for _ in range(animation_count):
                content_indicator = binary.read_u32(f)

                # skip 32, read as the size of the animation, irrelevant here
                binary.read_u32(f)

                filename_len = binary.read_u32(f)
                filename = f.read(filename_len).decode()

                if content_indicator == AnmContentIndicator.DCA:
                    animation = DCA.from_file(f)
                elif content_indicator == AnmContentIndicator.DCK:
                    animation = DCK.from_file(f)
                else:
                    print(
                        "Bundle has invalid content ID! Expected either DCK or DCA within bundle."
                    )
                    raise ValueError("Invalid-content-ID")

                animation.name = Path(filename).stem

                animations.append(animation)

        return cls(animations)
