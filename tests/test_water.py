import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from code.level import Level
from code.water import AnimatedWater


class WaterAnimationTests(unittest.TestCase):
    def make_water(self):
        self.images = []

        def load(path):
            image = SimpleNamespace(w=160, h=192, opacify=Mock(), clip_draw=Mock())
            self.images.append(image)
            return image

        with patch("pico2d.load_image", side_effect=load):
            return AnimatedWater()

    def test_gray_water_stays_static_and_only_blue_water_animates(self):
        water = self.make_water()
        pools = Level().water
        pools[1].has_blue = True
        water.update(0.2, pools)
        self.assertEqual([water.frame_for(p) for p in pools], [0, 1, 0])
        self.assertEqual([p.animation_time for p in pools], [0, 0.2, 0])
        water.update(5.8, pools)
        self.assertEqual(water.frame_for(pools[1]), 0)
        for _ in range(30):
            water.update(1 / 60, pools)
        self.assertEqual(water.frame_for(pools[1]), 0)

    def test_gray_and_blue_use_separate_images_and_valid_frames(self):
        water = self.make_water()
        pools = Level().water
        water.draw_surface(pools, 1900)
        self.assertTrue(water.gray_surface.clip_draw.called)
        water.blue_surface.clip_draw.assert_not_called()
        pools[1].has_blue = True
        for step in range(30):
            water.update(0.1, pools)
            water.draw_surface(pools, 1900)
        self.assertTrue(water.blue_surface.clip_draw.called)
        self.assertGreater(len({c.args[1] for c in water.blue_surface.clip_draw.call_args_list}), 1)
        self.assertEqual({c.args[1] for c in water.gray_surface.clip_draw.call_args_list}, {160})
        for image in self.images:
            for call in image.clip_draw.call_args_list:
                x, y, w, h, *_ = call.args
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + w, image.w)
                self.assertLessEqual(y + h, image.h)

    def test_offscreen_water_does_not_draw(self):
        water = self.make_water()
        water.draw_surface(Level().water, 0)
        for image in self.images:
            image.clip_draw.assert_not_called()
