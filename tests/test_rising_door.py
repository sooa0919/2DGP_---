import unittest
from unittest.mock import Mock, patch

from code.camera import Camera
from code.illustrated_level import IllustratedLevel
from code.level import Platform
from code.stage_art import StageArt
from code.stage_devices import RisingDoor


class RisingDoorTests(unittest.TestCase):
    def setUp(self):
        self.door = Platform(2882, 75, 2928, 486)
        self.motion = RisingDoor()

    def test_pan_precedes_slow_open_and_collision_tracks_the_remaining_gate(self):
        self.motion.update(.3, self.door, True)
        self.assertEqual(self.motion.offset, 0)
        self.assertEqual(self.motion.platform(self.door), self.door)
        self.motion.update(.65, self.door, True)
        self.assertGreater(self.motion.offset, 0)
        self.assertLess(self.motion.offset, 200)
        collider = self.motion.platform(self.door)
        self.assertEqual(collider.bottom, self.door.bottom + self.motion.offset)
        self.assertEqual(collider.top, self.door.top)
        self.motion.update(2, self.door, True)
        self.assertIsNone(self.motion.platform(self.door))

    def test_camera_focuses_on_door_then_returns_to_player(self):
        level = IllustratedLevel()
        player = Mock(x=3060, y=646)
        self.assertEqual(level.camera_target(player), (3060, 646))
        level.door_motion.update(RisingDoor.PAN_DURATION, level.door, True)
        self.assertEqual(level.camera_target(player), (2905, 280.5))
        level.door_motion.update(4, level.door, True)
        self.assertEqual(level.camera_target(player), (3060, 646))

    def test_camera_motion_moves_toward_the_gate_and_back(self):
        level = IllustratedLevel()
        player = Mock(x=3060, y=646)
        camera = Camera(1152, level.width, level.height)
        camera.snap_to(player.x, player.y)
        start_x, start_y = camera.x, camera.y
        for _ in range(60):
            level.door_motion.update(1/60, level.door, True)
            camera.follow(*level.camera_target(player), 1/60)
        self.assertLess(camera.x, start_x - 100)
        self.assertLess(camera.y, 20)
        for _ in range(240):
            level.door_motion.update(1/60, level.door, True)
            camera.follow(*level.camera_target(player), 1/60)
        self.assertAlmostEqual(camera.x, start_x, places=3)
        self.assertAlmostEqual(camera.y, start_y, places=3)

    def test_closing_stops_above_player_and_reset_cancels_sequence(self):
        self.motion.update(3, self.door, True)
        player = Platform(2890, 78, 2920, 145)
        self.motion.update(2, self.door, False, player)
        self.assertGreaterEqual(self.motion.platform(self.door).bottom, player.top)
        self.motion.update(2, self.door, False, Platform(2700, 78, 2760, 145))
        self.assertEqual(self.motion.platform(self.door), self.door)
        self.motion.update(.3, self.door, True)
        self.motion.reset()
        self.assertEqual(self.motion.camera_weight, 0)
        self.assertEqual(self.motion.platform(self.door), self.door)

    def test_opening_is_independent_of_frame_rate(self):
        values = []
        for fps in (30, 60, 120):
            motion = RisingDoor()
            for _ in range(round(fps * 1.2)):
                motion.update(1/fps, self.door, True)
            values.append((motion.offset, motion.camera_weight))
        for offset, weight in values[1:]:
            self.assertAlmostEqual(offset, values[0][0])
            self.assertAlmostEqual(weight, values[0][1])

    def test_gate_art_rises_into_ceiling_instead_of_disappearing_immediately(self):
        level = IllustratedLevel()
        level.door_switch.active = True
        level.door_motion.update(1, level.door, True)
        with patch('pico2d.load_image', return_value=Mock(w=1024, h=1008)):
            art = StageArt(level)
        with patch.object(art, 'sprite') as draw, patch('pico2d.draw_rectangle'):
            art.draw_devices(2300, 0)
            door = [c for c in draw.call_args_list if c.args[0] == 'door_on']
            self.assertEqual(len(door), 1)
            self.assertFalse(door[0].kwargs['gray'])
            self.assertEqual(door[0].kwargs['offset'], level.door_motion.offset)
            self.assertEqual(door[0].kwargs['trim_top'], level.door.top)

    def test_gate_changes_color_before_rising_and_returns_to_gray_when_canceled(self):
        level = IllustratedLevel()
        with patch('pico2d.load_image', return_value=Mock(w=1024, h=1008)):
            art = StageArt(level)
        with patch.object(art, 'sprite') as draw, patch('pico2d.draw_rectangle'):
            art.draw_devices(2300, 0)
            closed = [c for c in draw.call_args_list if c.args[0] == 'door'][-1]
            self.assertTrue(closed.kwargs['gray'])
            level.door_switch.active = True
            art.draw_devices(2300, 0)
            opened = [c for c in draw.call_args_list if c.args[0] == 'door_on'][-1]
            self.assertFalse(opened.kwargs['gray'])
            self.assertEqual(opened.kwargs['offset'], 0)
            level.door_switch.active = False
            draw.reset_mock()
            art.draw_devices(2300, 0)
            self.assertFalse(any(c.args[0] == 'door_on' for c in draw.call_args_list))
