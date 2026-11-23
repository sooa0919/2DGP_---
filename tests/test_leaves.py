import unittest
from unittest.mock import Mock, patch

from code.leaves import TitleLeaves


class TitleLeavesTests(unittest.TestCase):
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
