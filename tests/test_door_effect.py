import unittest
from unittest.mock import Mock, patch

from code.camera import Camera
from code.door_effect import DoorOpeningEffect, DoorEffectRenderer
from code.illustrated_level import IllustratedLevel
from code.level import Platform


class DoorEffectTests(unittest.TestCase):
    def test_effect_triggers_once_per_open_and_reset_clears_it(self):
        level = IllustratedLevel()
        player = Mock(left=0, right=100, grounded=False)
        level.update(.1, player)
        effect = level.door_effect
        self.assertEqual(effect.particles, [])
        level.door_switch.active = True
        level.update(.016, player)
        self.assertEqual(effect.openings, 1)
        self.assertEqual(len(effect.particles), 48)
        for p in effect.particles:
            self.assertIn(p.x, (level.door.left, level.door.right))
            self.assertLess(level.door.bottom, p.y)
            self.assertGreater(level.door.top, p.y)
        level.update(.1, player)
        self.assertEqual(effect.openings, 1)
        level.door_switch.active = False
        level.update(.01, player)
        level.door_switch.active = True
        level.update(.01, player)
        self.assertEqual(effect.openings, 2)
        level.reset()
        self.assertEqual(effect.shake_offset, (0, 0))
        self.assertEqual(effect.particles, [])

    def test_shake_and_debris_motion_are_independent_of_frame_rate_and_expire(self):
        positions = []
        door = Platform(200, 80, 250, 480)
        for fps in (30, 60, 120):
            effect = DoorOpeningEffect()
            effect.update(0, door, True)
            for _ in range(fps // 5):
                effect.update(1 / fps, door, True)
            positions.append((effect.shake_offset, effect.particles[0].position(effect.age)))
            self.assertLessEqual(abs(effect.shake_offset[0]), 7)
            self.assertNotEqual(effect.shake_offset, (0, 0))
            effect.update(2, door, True)
            self.assertEqual(effect.shake_offset, (0, 0))
            self.assertEqual(effect.particles, [])
        for offset, position in positions[1:]:
            for a, b in zip(offset + position, positions[0][0] + positions[0][1]):
                self.assertAlmostEqual(a, b)

    def test_shaken_view_stays_inside_map_and_does_not_move_camera_tracking(self):
        camera = Camera(1152, 4096, 1008)
        camera.x, camera.y = 2000, 200
        self.assertEqual(camera.view_position(5, -3), (2005, 197))
        self.assertEqual((camera.x, camera.y), (2000, 200))
        camera.snap_to(0, 0)
        self.assertEqual(camera.view_position(-7, -7), (0, 0))
        camera.snap_to(4096, 1008)
        self.assertEqual(camera.view_position(7, 7), (2944, 360))

    def test_dust_fades_and_finished_particles_stop_drawing(self):
        effect = DoorOpeningEffect()
        effect.update(.1, Platform(200, 80, 250, 480), True)
        with patch('pico2d.load_image', side_effect=[Mock(w=128, h=128), Mock(w=32, h=32)]):
            renderer = DoorEffectRenderer()
        renderer.draw(effect, 0, 0)
        self.assertTrue(renderer.dust.draw.called)
        self.assertTrue(renderer.chip.clip_composite_draw.called)
        effect.update(2, Platform(200, 80, 250, 480), True)
        renderer.dust.reset_mock()
        renderer.chip.reset_mock()
        renderer.draw(effect, 0, 0)
        renderer.dust.draw.assert_not_called()
        renderer.chip.clip_composite_draw.assert_not_called()
