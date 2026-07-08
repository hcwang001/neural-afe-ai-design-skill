#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> int:
    parser = argparse.ArgumentParser(description="Combine four PNG plots into a 2x2 panel.")
    parser.add_argument("images", nargs=4, help="Four input PNG files in panel order.")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path.")
    parser.add_argument("--gap", type=int, default=28, help="Gap between panels in pixels.")
    args = parser.parse_args()

    paths = [Path(p) for p in args.images]
    images = [Image.open(p).convert("RGB") for p in paths]
    width = max(img.width for img in images)
    height = max(img.height for img in images)
    canvas = Image.new("RGB", (2 * width + args.gap, 2 * height + args.gap), "white")
    positions = [(0, 0), (width + args.gap, 0), (0, height + args.gap), (width + args.gap, height + args.gap)]
    for img, pos in zip(images, positions):
        if img.size != (width, height):
            img = img.resize((width, height), Image.Resampling.LANCZOS)
        canvas.paste(img, pos)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, "PNG")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
