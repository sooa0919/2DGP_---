import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from code.level import Level
from code.water import AnimatedWater


class WaterAnimationTests(unittest.TestCase):
    def make_water(self):
        self.images = []

        def load(path):
            width, height = (160, 192) if "surface" in path else (640, 352)
            image = SimpleNamespace(w=width, h=height, opacify=Mock(), clip_draw=Mock())
            self.images.append(image)
            return image

        with patch("pico2d.load_image", side_effect=load):
            return AnimatedWater()

    def test_frames_advance_loop_and_do_not_depend_on_update_rate(self):
        water = self.make_water()
        water.update(0.2)
        self.assertEqual((water.surface_frame, water.fall_frame), (1, 2))
        water.update(5.8)
        self.assertEqual((water.surface_frame, water.fall_frame), (0, 0))
        for _ in range(30):
            water.update(1 / 60)
        split = (water.surface_frame, water.fall_frame)
        other = self.make_water()
        other.update(0.5)
        self.assertEqual(split, (other.surface_frame, other.fall_frame))

    def test_all_animation_frames_stay_within_the_supplied_sheets(self):
        water = self.make_water()
        level = Level()
        for frame in range(60):
            water.time = frame / 10
            water.draw_falls(level.waterfalls, 1900)
            water.draw_surface(level.water, level.waterfalls, 1900)
        for image in self.images:
            self.assertTrue(image.clip_draw.called)
            for call in image.clip_draw.call_args_list:
                x, y, w, h, *_ = call.args
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, image.w)
                self.assertLessEqual(y + h, image.h)

    def test_offscreen_water_does_not_draw(self):
        water = self.make_water()
        level = Level()
        water.draw_falls(level.waterfalls, 0)
        water.draw_surface(level.water, level.waterfalls, 0)
        for image in self.images:
            image.clip_draw.assert_not_called()
