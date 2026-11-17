import unittest

from code.level import Level
from code.scenery import PROP_BOUNDS


class SceneryTests(unittest.TestCase):
    def test_all_props_fit_on_a_dry_flat_surface(self):
        for index in (0, 1):
            level = Level(index)
            self.assertTrue(all(p.bottom == 0 for p in level.platforms))
            for name, x, y, scale in level.objects:
                self.assertFalse(name.startswith("Swamp/"))
                left, _, right, _ = PROP_BOUNDS[name]
                half = (right - left) * scale / 2
                self.assertTrue(any(p.top == y and p.left <= x - half
                                    and p.right >= x + half for p in level.platforms),
                                (index, name, x, y))
                self.assertFalse(any(w.left < x < w.right for w in level.water))

    def test_water_is_exactly_one_tile_deep(self):
        for index in (0, 1):
            level = Level(index)
            for pool in level.water:
                self.assertEqual(pool.top - pool.bottom, 32)
                self.assertTrue(any(p.left == pool.left and p.right == pool.right
                                    and p.top == pool.bottom for p in level.platforms))
