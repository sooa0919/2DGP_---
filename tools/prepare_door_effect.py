"""Generate small antialiased, grayscale game-particle textures."""
from pathlib import Path
import math

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent


def main():
    folder = ROOT / 'image/effects'
    folder.mkdir(exist_ok=True)
    dust = Image.new('RGBA', (128, 128))
    pixels = []
    lobes = ((53, 59, 39), (76, 57, 30), (64, 78, 27), (40, 76, 24))
    for y in range(128):
        for x in range(128):
            density = max(max(0, 1 - math.hypot(x-cx, y-cy) / radius) ** 1.7
                          for cx, cy, radius in lobes)
            pixels.append((182, 182, 182, round(205 * density)))
    dust.putdata(pixels)
    dust.save(folder / 'door_dust.png')
    chip = Image.new('RGBA', (128, 128))
    draw = ImageDraw.Draw(chip)
    draw.polygon(((17, 44), (50, 18), (96, 31), (113, 76), (81, 111), (29, 96)),
                 fill=(112, 112, 112, 255), outline=(65, 65, 65, 255), width=7)
    draw.polygon(((50, 25), (91, 36), (64, 60), (24, 46)), fill=(168, 168, 168, 255))
    chip.resize((32, 32), Image.Resampling.LANCZOS).save(folder / 'door_chip.png')


if __name__ == '__main__':
    main()
