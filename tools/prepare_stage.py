"""Prepare intact terrain, decoration, and gimmick layers at shared coordinates."""
from pathlib import Path
import json

from PIL import Image, ImageOps, ImageChops

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

    def save(name, image, bounds, behind_terrain=False):
        crop = image.crop(bounds)
        if behind_terrain:
            # Clip the WATER layer only. This lets it tint the player while
            # keeping opaque tiles in front, without changing any tile pixels.
            visible = ImageOps.invert(terrain.getchannel('A').crop(bounds))
            crop.putalpha(ImageChops.multiply(crop.getchannel('A'), visible))
        crop.save(folder / f'{name}.png')
        gray = ImageOps.grayscale(crop).convert('RGBA')
        gray.putalpha(crop.getchannel('A'))
        gray.save(folder / f'{name}_gray.png')
        left, top, right, bottom = bounds
        manifest[name] = [left, STAGE_SIZE[1] - bottom, right, STAGE_SIZE[1] - top]

    # All three frames use a common crop so their positions never jitter.
    water_bounds = (150, 250, 555, 1008)
    for frame in range(1, 4):
        save(f'water{frame}', sheets[f'water{frame}'], water_bounds, behind_terrain=True)
    save('pool', sheets['water_tile'], sheets['water_tile'].getbbox(), behind_terrain=True)
    for name, bounds in REGIONS.items():
        save(name, sheets['color_system'], bounds)
    door = sheets['color_system'].crop(REGIONS['door'])
    colored_door = ImageOps.colorize(ImageOps.grayscale(door), (62, 47, 26), (223, 193, 118)).convert('RGBA')
    colored_door.putalpha(door.getchannel('A'))
    colored_door.save(folder / 'door_on.png')
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
    # The central tree was previously traced by hand. Read its solid silhouette
    # directly from the clean tile layer, including the switch's curved ledge.
    alpha = terrain.getchannel('A')
    colliders = []
    previous = {}
    for left in range(2400, 3500, 4):
        runs = []
        start = None
        for y in range(609):
            solid = y < 608 and alpha.getpixel((left + 2, y)) >= 160
            if solid and start is None:
                start = y
            elif not solid and start is not None:
                if y - start >= 12:  # Ignore detached decorative specks/shoots.
                    runs.append((1008 - y, 1008 - start))
                start = None
        current = {}
        for bottom, top in runs:
            key = (bottom, top)
            old = previous.get(key)
            if old is not None:
                colliders[old][2] = left + 4
                current[key] = old
            else:
                current[key] = len(colliders)
                colliders.append([left, bottom, left + 4, top])
        previous = current
    (folder / 'central_tree_collision.json').write_text(json.dumps(colliders), encoding='utf-8')
    (folder / 'layout.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
