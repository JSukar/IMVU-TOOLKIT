#!/usr/bin/env python3
"""Build a transparent Windows .ico from assets/imvu-toolkit-logo.png."""

import sys
from pathlib import Path

from PIL import Image

ICON_SIZES = (256, 128, 64, 48, 32, 16)


def icon_frame(source: Image.Image, size: int) -> Image.Image:
    """Fit source on a square transparent canvas (preserves alpha)."""
    frame = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    scaled = source.copy()
    scaled.thumbnail((size, size), Image.Resampling.LANCZOS)
    x = (size - scaled.width) // 2
    y = (size - scaled.height) // 2
    frame.paste(scaled, (x, y), scaled)
    return frame


def png_to_ico(png_path: Path, ico_path: Path) -> None:
    source = Image.open(png_path).convert("RGBA")
    frames = [icon_frame(source, size) for size in ICON_SIZES]
    frames[0].save(
        ico_path,
        format="ICO",
        sizes=[frame.size for frame in frames],
        append_images=frames[1:],
    )


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    png_path = root / "assets" / "imvu-toolkit-logo.png"
    ico_path = root / "assets" / "imvu-toolkit-logo.ico"

    if not png_path.exists():
        raise SystemExit("Missing logo PNG: %s" % png_path)

    png_to_ico(png_path, ico_path)
    sys.stdout.write("Wrote %s from %s\n" % (ico_path, png_path.name))


if __name__ == "__main__":
    main()
