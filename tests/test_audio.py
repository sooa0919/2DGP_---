import unittest
from unittest.mock import Mock, patch

from code.audio import MusicManager


class MusicTests(unittest.TestCase):
    def test_click_sound_loads_once_uses_effects_volume_and_leaves_bgm_alone(self):
        bgm, click = Mock(), Mock()
        with patch('pico2d.load_music', return_value=bgm), \
             patch('pico2d.load_wav', return_value=click) as load, \
             patch('pico2d.Mix_HaltChannel') as halt:
            music = MusicManager()
            music.play('title')
            music.play_click()
            click.set_volume.assert_called_with(102)
            music.set_effects_volume(0)
            music.play_click()
            click.set_volume.assert_called_with(0)
            music.play_click(50)
            click.set_volume.assert_called_with(64)
            self.assertEqual(click.play.call_count, 3)
            load.assert_called_once_with(str(music.CLICK_PATH))
            bgm.repeat_play.assert_called_once()
            bgm.set_volume.assert_called_once_with(102)
            music.close()
            halt.assert_called_once_with(-1)

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
            stage.set_volume.assert_called_with(26)
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
            stage.set_volume.assert_called_with(26)
            music.set_volume(120)
            stage.set_volume.assert_called_with(32)
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
