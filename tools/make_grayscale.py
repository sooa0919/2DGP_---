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
    root = BACKGROUND_ROOT.parent
    sources.extend((p, OUTPUT_ROOT / "tiles" / p.name)
                   for p in (BACKGROUND_ROOT / "tile").glob("Tile_*.png"))
    sources.extend((BACKGROUND_ROOT / "tile" / name, OUTPUT_ROOT / "water" / target)
                   for name, target in (("GandalfHardcore Water Tiles sheet.png", "surface.png"),))
    sources.extend((p, OUTPUT_ROOT / "objects" / p.relative_to(root / "object" / "Objects"))
                   for p in (root / "object" / "Objects").glob("*/*.png"))
    sources.extend((root / "character" / state / f"{state}_blue.png",
                    OUTPUT_ROOT / "character" / f"{state}.png")
                   for state in ("idle", "run"))
    gandalf = root / "object" / "GandalfHardcore FREE Platformer Assets" / "GandalfHardcore FREE Platformer Assets"
    sources.append((gandalf / "Angel Statue.png", OUTPUT_ROOT / "objects" / "Ruins" / "statue.png"))
    for source, destination in sources:
        with Image.open(source) as original:
            rgba = original.convert("RGBA")
            grayscale = ImageOps.grayscale(rgba).convert("RGBA")
            grayscale.putalpha(rgba.getchannel("A"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            grayscale.save(destination)
        print(f"Generated: {destination.relative_to(BACKGROUND_ROOT)}")
    with Image.open(gandalf / "Decor.png") as decor:
        for name, box in (("low", (32, 176, 96, 192)), ("moss", (0, 272, 96, 320))):
            rock = decor.convert("RGBA").crop(box)
            gray = ImageOps.grayscale(rock).convert("RGBA")
            gray.putalpha(rock.getchannel("A"))
            folder = OUTPUT_ROOT / "objects" / "Rock"
            folder.mkdir(parents=True, exist_ok=True)
            gray.save(folder / f"{name}.png")


if __name__ == "__main__":
    main()
