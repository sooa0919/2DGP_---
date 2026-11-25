import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops, ImageOps

from code.stage_art import StageArt
from tools import preview_levels as renderer
import numpy as np


ROOT = Path(__file__).resolve().parent.parent


class StageArtTests(unittest.TestCase):
    def test_water_overlay_is_hidden_by_tiles_without_changing_tile_alpha(self):
        import json
        folder = ROOT / 'image/background/stage1'
        layout = json.loads((folder / 'layout.json').read_text(encoding='utf-8'))
        with Image.open(ROOT / 'image/background/tile/tile.png') as source:
            terrain_alpha = source.convert('RGBA').resize((4096, 1008), Image.Resampling.LANCZOS).getchannel('A')
        for name in ('water1', 'water2', 'water3', 'pool'):
            left, bottom, right, top = layout[name]
            bounds = (left, 1008-top, right, 1008-bottom)
            original_name = 'water_tile' if name == 'pool' else name
            with Image.open(ROOT / f'image/background/tile/{original_name}.png') as source:
                alpha = source.convert('RGBA').resize((4096, 1008), Image.Resampling.LANCZOS).crop(bounds).getchannel('A')
            expected = ImageChops.multiply(alpha, ImageOps.invert(terrain_alpha.crop(bounds)))
            with Image.open(folder / f'{name}.png') as overlay:
                self.assertTrue(np.array_equal(np.array(overlay.getchannel('A')), np.array(expected)))

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

    def test_terrain_is_an_exact_grayscale_copy_of_tile_with_original_alpha(self):
        from tools.prepare_stage import grayscale
        with Image.open(ROOT / 'image/background/tile/tile.png') as source:
            expected = grayscale(source.convert('RGBA').resize((4096, 1008), Image.Resampling.LANCZOS))
        actual = Image.new('RGBA', expected.size)
        for i in range(4):
            with Image.open(ROOT / f'image/background/stage1/stage_{i}.png') as chunk:
                actual.paste(chunk, (i * 1024, 0))
        self.assertTrue(np.array_equal(np.array(actual), np.array(expected)))
        with Image.open(ROOT / 'image/background/stage1/stage_3_source.png') as colored:
            self.assertTrue(np.array_equal(np.array(colored.getchannel('A')),
                                           np.array(actual.crop((3072, 0, 4096, 1008)).getchannel('A'))))

    def test_scrolled_view_has_no_seams_or_vertical_offset(self):
        original_canvas = renderer.canvas
        try:
            with patch('pico2d.load_image', side_effect=renderer.Sprite):
                art = StageArt()
            expected_world = Image.new('RGB', (4096, 1008), (32, 40, 48))
            for i, sprite in enumerate(art.objects):
                expected_world.paste(sprite.image, (i * 1024, 0), sprite.image)
            for name in ('water1', 'pool', 'leaf_0', 'leaf_1', 'leaf_2', 'leaf_3',
                         'lamp_upper', 'door', 'lamp_door', 'ropes', 'elevator', 'lamp_elevator'):
                left, bottom, right, top = art.layout[name]
                sprite = art.sprites[name].image
                expected_world.paste(sprite, (left, 1008-top), sprite)
            chunks = art.chunks[:3] + [art.source_chunk]
            for i, sprite in enumerate(chunks):
                expected_world.paste(sprite.image, (i * 1024, 0), sprite.image)
            for camera_x, camera_y in ((0, 0), (1000, 200), (2944, 360)):
                renderer.canvas = Image.new('RGB', (1152, 648), (32, 40, 48))
                art.draw(camera_x, camera_y)
                expected = expected_world.crop((camera_x, 1008-camera_y-648,
                                                camera_x+1152, 1008-camera_y))
                delta = np.abs(np.array(renderer.canvas).astype(float) - np.array(expected).astype(float))
                self.assertLess(delta.mean(), .2)
        finally:
            renderer.canvas = original_canvas


if __name__ == '__main__':
    unittest.main()
