import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops

from code.stage_art import StageArt
from tools import preview_levels as renderer
import numpy as np


ROOT = Path(__file__).resolve().parent.parent


class StageArtTests(unittest.TestCase):
    def test_static_background_contains_no_baked_waterfall_frames(self):
        with Image.open(ROOT / 'image/background/stage1/stage_0.png') as chunk:
            # Mid-air waterfall section: all three frame silhouettes must be
            # absent, including their thin antialiased edge remnants.
            self.assertEqual(chunk.crop((300, 350, 390, 500)).getchannel('A').getextrema(), (0, 0))

    def test_background_chunks_are_gray_and_keep_transparency(self):
        for i in range(4):
            with Image.open(ROOT / f'image/background/stage1/stage_{i}.png') as chunk:
                self.assertEqual(chunk.size, (1024, 1008))
                pixels = np.array(chunk)
                opaque = pixels[:, :, 3] > 0
                self.assertTrue(opaque.any())
                self.assertTrue((pixels[:, :, 0][opaque] == pixels[:, :, 1][opaque]).all())
                self.assertTrue((pixels[:, :, 1][opaque] == pixels[:, :, 2][opaque]).all())
                self.assertTrue((pixels[:, :, 3] == 0).any())

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
                             'lamp_upper', 'door', 'lamp_door', 'ropes', 'elevator', 'lamp_elevator', 'source_ceiling'):
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
