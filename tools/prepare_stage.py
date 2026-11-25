"""Prepare the supplied stage without rearranging its artwork."""
from pathlib import Path
import json

import numpy as np
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


def remove_layer(composite, layer):
    """Undo source-over where possible; opaque layer pixels become transparent."""
    result = np.asarray(composite).astype(np.float32) / 255
    foreground = np.asarray(layer).astype(np.float32) / 255
    alpha = foreground[:, :, 3:4]
    base_alpha = np.clip((result[:, :, 3:4] - alpha) / np.maximum(1 - alpha, .0001), 0, 1)
    rgb = (result[:, :, :3] * result[:, :, 3:4] - foreground[:, :, :3] * alpha)
    rgb /= np.maximum((1 - alpha) * base_alpha, .0001)
    base_alpha[alpha >= .995] = 0
    return Image.fromarray(np.rint(np.concatenate((np.clip(rgb, 0, 1), base_alpha), axis=2) * 255).astype('uint8'))


def main():
    folder = ROOT / 'image/background/stage1'
    folder.mkdir(exist_ok=True)
    with Image.open(ROOT / 'image/background/tile/stage1_preview.png') as image:
        stage = image.convert('RGBA').resize(STAGE_SIZE, Image.Resampling.LANCZOS)
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
    for name in ('color_system', 'water1', 'water_tile'):
        stage = remove_layer(stage, sheets[name])
    # Restore decoration hidden behind opaque moving devices (notably the
    # tree canopy behind the elevator). Never bake the old platform back in.
    stage = Image.alpha_composite(sheets['object'], stage)
    for left in range(0, stage.width, CHUNK_WIDTH):
        stage.crop((left, 0, min(left + CHUNK_WIDTH, stage.width), stage.height)).save(
            folder / f'stage_{left // CHUNK_WIDTH}.png')
    (folder / 'layout.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
