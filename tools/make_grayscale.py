"""Generate grayscale scenery with Pillow while preserving source images."""

from pathlib import Path

from PIL import Image, ImageOps


BACKGROUND_ROOT = Path(__file__).resolve().parent.parent / "image" / "background"
OUTPUT_ROOT = BACKGROUND_ROOT / "grayscale"


def main():
    sources = [
        (BACKGROUND_ROOT / "background_layer" / "background3_jungle2" / f"plx-{i}.png",
         OUTPUT_ROOT / "background3_jungle2" / f"plx-{i}.png")
        for i in range(1, 6)
    ]
    sources.append((BACKGROUND_ROOT / "tile" / "Tileset.png", OUTPUT_ROOT / "Tileset.png"))
    for source, destination in sources:
        with Image.open(source) as original:
            rgba = original.convert("RGBA")
            grayscale = ImageOps.grayscale(rgba).convert("RGBA")
            grayscale.putalpha(rgba.getchannel("A"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            grayscale.save(destination)
        print(f"Generated: {destination.relative_to(BACKGROUND_ROOT)}")


if __name__ == "__main__":
    main()
