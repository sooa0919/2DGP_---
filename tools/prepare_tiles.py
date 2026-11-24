"""Extract runtime tiles from the supplied illustrated sheets; keep sources intact."""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent


def matte(image):
    image = image.convert('RGBA')
    pixels = list(image.get_flattened_data() if hasattr(image, 'get_flattened_data') else image.getdata())
    image.putdata([(r, g, b, 0 if max(r, g, b) < 80 and max(r, g, b) - min(r, g, b) < 30 else a)
                   for r, g, b, a in pixels])
    return image


def main():
    sheet = Image.open(ROOT / 'image/background/tile/Tileset.png').convert('RGBA')
    folder = ROOT / 'image/background/tutorial_tiles'
    folder.mkdir(exist_ok=True)
    for index in range(8):
        x = 51 + index * 100
        dirt = sheet.crop((x + 5, 58, x + 79, 132)).resize((64, 64), Image.Resampling.LANCZOS)
        grass = matte(sheet.crop((x, 192, x + 87, 277))).resize((64, 64), Image.Resampling.LANCZOS)
        stone = sheet.crop((x + 5, 366 if index in (5, 6) else 338, x + 79, 407)).resize((64, 64), Image.Resampling.LANCZOS)
        for name, tile in (('dirt', dirt), ('grass', grass), ('stone', stone)):
            gray = ImageOps.grayscale(tile).convert('RGBA')
            gray.putalpha(tile.getchannel('A'))
            gray.save(folder / f'{name}_{index}.png')
    for frame, y in enumerate((591, 643, 694)):
        tile = sheet.crop((111, y, 173, y + 46)).resize((64, 48), Image.Resampling.LANCZOS)
        tile.save(folder / f'water_{frame}.png')
        if frame == 0:
            ImageOps.grayscale(tile).convert('RGBA').save(folder / 'water_gray.png')
    cap = matte(sheet.crop((51, 192, 138, 222))).resize((64, 20), Image.Resampling.LANCZOS)
    green = ImageOps.colorize(ImageOps.grayscale(cap), (22, 64, 32), (115, 213, 118)).convert('RGBA')
    green.putalpha(cap.getchannel('A'))
    green.save(folder / 'vine_cap.png')
    emblem = matte(sheet.crop((350, 332, 437, 415)))
    emblem_gray = ImageOps.grayscale(emblem)
    for name, low, high in (('lamp', (50, 50, 50), (195, 195, 195)),
                            ('lamp_on', (92, 68, 20), (255, 222, 98))):
        tile = ImageOps.colorize(emblem_gray, low, high).convert('RGBA')
        tile.putalpha(emblem.getchannel('A'))
        tile.save(folder / f'{name}.png')
    fall = Image.open(ROOT / 'image/background/tile/tileset_water.webp')
    for frame, y in enumerate((32, 365, 698)):
        tile = matte(fall.crop((96, y, 207, y + 288)))
        tile.save(folder / f'fall_{frame}.png')
        if frame == 0:
            gray = ImageOps.grayscale(tile).convert('RGBA')
            gray.putalpha(tile.getchannel('A'))
            gray.save(folder / 'fall_gray.png')
    decorations = {'rock': (1225, 317, 1345, 394), 'rocks': (1360, 316, 1502, 394),
                   'sprout': (1214, 240, 1299, 286), 'flowers': (1315, 234, 1394, 286),
                   'ledge': (1006, 341, 1162, 394)}
    for name, bounds in decorations.items():
        crop = matte(sheet.crop(bounds))
        crop = crop.crop(crop.getchannel('A').getbbox())
        gray = ImageOps.grayscale(crop).convert('RGBA')
        gray.putalpha(crop.getchannel('A'))
        gray.save(folder / f'{name}.png')


if __name__ == '__main__':
    main()
