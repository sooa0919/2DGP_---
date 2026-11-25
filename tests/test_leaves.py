import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from PIL import Image

from code.leaves import TitleLeaves


class TitleLeavesTests(unittest.TestCase):
    def test_all_nine_high_resolution_frames_stay_inside_the_padded_atlas(self):
        folder = Path(__file__).resolve().parent.parent / 'image/background/leaves'
        with Image.open(folder / 'leaves.png') as atlas:
            width, height = atlas.size
            with patch('pico2d.load_image', return_value=Mock(w=width, h=height)):
                leaves = TitleLeaves()
            self.assertEqual((leaves.frames['width'], leaves.frames['height']), (2304, 1296))
            rectangles = []
            for duration in leaves.frames['durations']:
                leaves.draw()
                x, y, w, h = leaves.sheet.clip_draw.call_args.args[:4]
                self.assertGreaterEqual(x, 4)
                self.assertGreaterEqual(y, 4)
                self.assertLessEqual(x + w + 4, width)
                self.assertLessEqual(y + h + 4, height)
                rectangles.append((x, y, w, h))
                leaves.update(duration)
            self.assertEqual(len(set(rectangles)), 9)
            self.assertEqual(leaves.frame, 0)
            alpha = atlas.crop((4, 4, 2308, 1300)).getchannel('A')
            self.assertTrue(any(0 < value < 255 for count, value in alpha.getcolors(256)))
            self.assertEqual(atlas.crop((0, 0, width, 4)).getchannel('A').getextrema(), (0, 0))

    def test_every_supplied_frame_repeats_independent_of_frame_rate(self):
        with patch('pico2d.load_image', return_value=Mock()):
            leaves = TitleLeaves()
        frames = []
        for duration in leaves.frames['durations']:
            frames.append(leaves.frame)
            leaves.update(duration)
        self.assertEqual(frames, list(range(9)))
        self.assertEqual(leaves.frame, 0)
        for fps in (30, 60, 120):
            leaves.time = 0
            for _ in range(fps):
                leaves.update(1 / fps)
            self.assertEqual(leaves.frame, 6)
