"""One looping BGM at a time, shared by the title and tutorial."""
import pico2d

from .settings import ROOT


class MusicManager:
    CLICK_PATH = ROOT / 'sound/sound/ui_sound/UI_Click_Bubble_Pop_V01.wav'
    TRACKS = {
        'title': ROOT / 'sound/sound/title_bgm/placidplace-fantasy-lucid-forestpart-two-49992.mp3',
        'tutorial': ROOT / 'sound/sound/bgm/stage_1.mp3',
    }

    def __init__(self):
        self.tracks = {}
        self.current = None
        self.volume = 80
        self.effects_volume = 80
        self.click_sound = None
        self.click_loaded = False

    def set_effects_volume(self, value):
        self.effects_volume = max(0, min(100, value))
        if self.click_sound is not None:
            self.click_sound.set_volume(round(self.effects_volume * 128 / 100))

    def play_click(self, volume=None):
        if volume is not None:
            self.set_effects_volume(volume)
        if not self.click_loaded:
            self.click_loaded = True
            try:
                self.click_sound = pico2d.load_wav(str(self.CLICK_PATH))
            except OSError:
                return
        if self.click_sound is not None:
            self.click_sound.set_volume(round(self.effects_volume * 128 / 100))
            self.click_sound.play()

    def play(self, scene):
        if scene == self.current:
            return
        if scene not in self.tracks:
            try:
                self.tracks[scene] = pico2d.load_music(str(self.TRACKS[scene]))
            except OSError:
                # A computer without an audio device can still run the game.
                self.tracks[scene] = None
        if self.current is not None and self.tracks[self.current] is not None:
            self.tracks[self.current].stop()
        self.current = scene
        track = self.tracks[scene]
        if track is not None:
            track.set_volume(round(self.volume * 128 / 100))
            track.repeat_play()

    def set_volume(self, value):
        value = max(0, min(100, value))
        if self.volume == value:
            return
        self.volume = value
        track = self.tracks.get(self.current)
        if track is not None:
            track.set_volume(round(value * 128 / 100))

    def close(self):
        if self.click_sound is not None:
            pico2d.Mix_HaltChannel(-1)
            self.click_sound = None
        track = self.tracks.get(self.current)
        if track is not None:
            track.stop()
        self.current = None
        self.tracks.clear()
