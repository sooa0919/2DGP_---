import unittest
from unittest.mock import Mock, patch

from code.audio import MusicManager


class MusicTests(unittest.TestCase):
    def test_scene_changes_loop_correct_tracks_without_restarting_on_repeat(self):
        title, stage = Mock(), Mock()
        with patch('pico2d.load_music', side_effect=[title, stage]) as load:
            music = MusicManager()
            music.play('title')
            music.play('title')
            title.repeat_play.assert_called_once()
            title.set_volume.assert_called_with(102)
            music.play('tutorial')
            title.stop.assert_called_once()
            stage.repeat_play.assert_called_once()
            music.play('title')
            stage.stop.assert_called_once()
            self.assertEqual(title.repeat_play.call_count, 2)
            self.assertEqual([call.args[0] for call in load.call_args_list],
                             [str(music.TRACKS['title']), str(music.TRACKS['tutorial'])])
            music.close()
        self.assertEqual(music.tracks, {})
        self.assertIsNone(music.current)

    def test_volume_is_applied_live_and_preserved_across_scenes(self):
        title, stage = Mock(), Mock()
        with patch('pico2d.load_music', side_effect=[title, stage]):
            music = MusicManager()
            music.play('title')
            music.set_volume(50)
            title.set_volume.assert_called_with(64)
            music.set_volume(0)
            title.set_volume.assert_called_with(0)
            music.play('tutorial')
            stage.set_volume.assert_called_with(0)
            music.set_volume(80)
            stage.set_volume.assert_called_with(102)
            music.set_volume(120)
            stage.set_volume.assert_called_with(128)
            stage.repeat_play.assert_called_once()

    def test_missing_audio_device_does_not_interrupt_game_or_retry_each_frame(self):
        with patch('pico2d.load_music', side_effect=OSError) as load:
            music = MusicManager()
            music.play('title')
            music.play('title')
            music.play('tutorial')
            music.play('title')
            music.set_volume(0)
            music.close()
        self.assertEqual(load.call_count, 2)
