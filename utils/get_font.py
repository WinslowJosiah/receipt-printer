import os
import pathlib
from typing import BinaryIO, TypeAlias

from PIL import ImageFont


StrOrBytesPath: TypeAlias = (
    str | bytes | os.PathLike[str] | os.PathLike[bytes]
)


def get_font(
    file: str,
    font: StrOrBytesPath | BinaryIO | None = None,
    size: float = 10,
    *args,
    **kwargs,
):
    try:
        return ImageFont.truetype(font, size, *args, **kwargs)
    except OSError:
        filedir = pathlib.Path(file).parent
        return ImageFont.truetype(
            filedir.joinpath("fonts").joinpath(font),
            size, *args, **kwargs,
        )
