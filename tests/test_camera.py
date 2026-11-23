import unittest

from code.camera import Camera


class SmoothCameraTests(unittest.TestCase):
    def test_camera_lags_in_both_axes_then_catches_up_without_overshoot(self):
        camera = Camera(1152, 4096, 1536)
        camera.follow(1000, 700, 1 / 60)
        self.assertGreater(camera.x, 0)
        self.assertLess(camera.x, 424)
        self.assertGreater(camera.y, 0)
        self.assertLess(camera.y, 376)
        for _ in range(120):
            camera.follow(1000, 700, 1 / 60)
        self.assertAlmostEqual(camera.x, 424, places=4)
        self.assertAlmostEqual(camera.y, 376, places=4)
        self.assertLessEqual(camera.x, 424)
        self.assertLessEqual(camera.y, 376)

    def test_response_is_independent_of_frame_rate(self):
        values = []
        for fps in (30, 60, 120):
            camera = Camera(1152, 4096, 1536)
            for _ in range(fps):
                camera.follow(1000, 700, 1 / fps)
            values.append((camera.x, camera.y))
        for value in values[1:]:
            self.assertAlmostEqual(value[0], values[0][0])
            self.assertAlmostEqual(value[1], values[0][1])

    def test_zero_dt_and_reset_snap_and_map_edges(self):
        camera = Camera(1152, 4096, 1536)
        camera.follow(1000, 700, 0)
        self.assertEqual((camera.x, camera.y), (0, 0))
        camera.snap_to(4096, 1536)
        self.assertEqual((camera.x, camera.y), (2944, 888))
        camera.follow(80, 132, 1 / 60)
        self.assertEqual((camera.x, camera.y), (0, 0))
        camera.snap_to(-100, -100)
        self.assertEqual((camera.x, camera.y), (0, 0))
