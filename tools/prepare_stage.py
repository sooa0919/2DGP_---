"""Prepare intact terrain, decoration, and gimmick layers at shared coordinates."""
from pathlib import Path
import json

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
STAGE_SIZE = (4096, 1008)
CHUNK_WIDTH = 1024

# Rectangles on the shared canvas, measured from its top-left corner.
REGIONS = {
    'leaf_0': (1510, 790, 1705, 865),
    'leaf_1': (1830, 790, 2030, 865),
    'leaf_2': (2135, 790, 2330, 865),
    'leaf_3': (2395, 375, 2590, 455),
    'lamp_upper': (3010, 290, 3120, 410),
    'door': (2870, 505, 2940, 955),
    'lamp_door': (3110, 510, 3235, 710),
    'ropes': (3400, 0, 3650, 830),
    'elevator': (3400, 830, 3650, 910),
    'lamp_elevator': (3645, 835, 3735, 945),
}


def grayscale(image):
    result = ImageOps.grayscale(image).convert('RGBA')
    result.putalpha(image.getchannel('A'))
    return result


def main():
    folder = ROOT / 'image/background/stage1'
    folder.mkdir(exist_ok=True)
    with Image.open(ROOT / 'image/background/tile/tile.png') as image:
        terrain = image.convert('RGBA').resize(STAGE_SIZE, Image.Resampling.LANCZOS)
    stage = grayscale(terrain)
    sheets = {}
    for name in ('water1', 'water2', 'water3', 'water_tile', 'color_system', 'object'):
        with Image.open(ROOT / f'image/background/tile/{name}.png') as image:
            sheets[name] = image.convert('RGBA').resize(STAGE_SIZE, Image.Resampling.LANCZOS)
    manifest = {}

    def save(name, image, bounds):
        crop = image.crop(bounds)
        crop.save(folder / f'{name}.png')
        gray = ImageOps.grayscale(crop).convert('RGBA')
        gray.putalpha(crop.getchannel('A'))
        gray.save(folder / f'{name}_gray.png')
        left, top, right, bottom = bounds
        manifest[name] = [left, STAGE_SIZE[1] - bottom, right, STAGE_SIZE[1] - top]

    # All three frames use a common crop so their positions never jitter.
    water_bounds = (150, 250, 555, 1008)
    for frame in range(1, 4):
        save(f'water{frame}', sheets[f'water{frame}'], water_bounds)
    save('pool', sheets['water_tile'], sheets['water_tile'].getbbox())
    for name, bounds in REGIONS.items():
        save(name, sheets['color_system'], bounds)
    ceiling_bounds = (3850, 515, 3935, 610)
    save('source_ceiling', terrain, ceiling_bounds)
    objects = grayscale(sheets['object'])
    # Tile pixels and alpha are never erased, dilated, repaired or sampled from
    # neighboring tiles. Objects and gimmicks are separate layers behind them.
    for left in range(0, stage.width, CHUNK_WIDTH):
        bounds = (left, 0, min(left + CHUNK_WIDTH, stage.width), stage.height)
        index = left // CHUNK_WIDTH
        stage.crop(bounds).save(folder / f'stage_{index}.png')
        objects.crop(bounds).save(folder / f'objects_{index}.png')
    # This source belongs to tile.png itself. Switch only its original colors;
    # both versions have exactly the same terrain shape and alpha.
    colored_source = stage.copy()
    colored_source.paste(terrain.crop(ceiling_bounds), ceiling_bounds[:2])
    colored_source.crop((3072, 0, 4096, 1008)).save(folder / 'stage_3_source.png')
    (folder / 'layout.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
