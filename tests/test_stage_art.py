import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops

from code.stage_art import StageArt
from tools import preview_levels as renderer
import numpy as np


ROOT = Path(__file__).resolve().parent.parent


class StageArtTests(unittest.TestCase):
    def test_colored_layers_reassemble_to_the_supplied_preview(self):
        with Image.open(ROOT / 'image/background/tile/stage1_preview.png') as source:
            expected = source.convert('RGBA').resize(
                (4096, 1008), Image.Resampling.LANCZOS)
        actual = Image.new('RGBA', expected.size)
        for i in range(4):
            with Image.open(ROOT / f'image/background/stage1/stage_{i}.png') as chunk:
                actual.paste(chunk, (i * 1024, 0))
        import json
        layout = json.loads((ROOT / 'image/background/stage1/layout.json').read_text())
        for name in ('water1', 'pool', 'leaf_0', 'leaf_1', 'leaf_2', 'leaf_3',
                     'lamp_upper', 'door', 'lamp_door', 'ropes', 'elevator', 'lamp_elevator'):
            left, bottom, right, top = layout[name]
            with Image.open(ROOT / f'image/background/stage1/{name}.png') as sprite:
                actual.alpha_composite(sprite, (left, 1008 - top))
        # Inverting rounded translucent edge pixels can differ by a few levels.
        back = Image.new('RGBA', actual.size, (32, 40, 48, 255))
        a = np.array(Image.alpha_composite(back, actual)).astype(float)
        b = np.array(Image.alpha_composite(back, expected)).astype(float)
        self.assertLess(np.abs(a-b).mean(), 1.0)

    def test_scrolled_view_has_no_seams_or_vertical_offset(self):
        original_canvas = renderer.canvas
        try:
            with patch('pico2d.load_image', side_effect=renderer.Sprite):
                art = StageArt()
            for camera_x, camera_y in ((0, 0), (1000, 200), (2944, 360)):
                renderer.canvas = Image.new('RGB', (1152, 648), (32, 40, 48))
                art.draw(camera_x, camera_y)
                expected = Image.new('RGB', (1152, 648), (32, 40, 48))
                stage = Image.new('RGBA', (4096, 1008))
                for i, sprite in enumerate(art.chunks):
                    stage.paste(sprite.image, (i * 1024, 0))
                for name in ('water1', 'pool', 'leaf_0', 'leaf_1', 'leaf_2', 'leaf_3',
                             'lamp_upper', 'door', 'lamp_door', 'ropes', 'elevator', 'lamp_elevator'):
                    left, bottom, right, top = art.layout[name]
                    sprite = art.sprites[name].image
                    # Match pico2d's regular alpha-blended sprite layers.
                    region = stage.crop((left, 1008-top, right, 1008-bottom))
                    region.alpha_composite(sprite)
                    stage.paste(region, (left, 1008-top))
                crop = stage.crop((camera_x, 1008 - camera_y - 648,
                                   camera_x + 1152, 1008 - camera_y))
                expected.paste(crop, (0, 0), crop)
                # Independent per-sprite alpha rounding may differ at edges.
                delta = np.abs(np.array(renderer.canvas).astype(float) - np.array(expected).astype(float))
                self.assertLess(delta.mean(), .2)
        finally:
            renderer.canvas = original_canvas


if __name__ == '__main__':
    unittest.main()
