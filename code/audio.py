"""One looping BGM at a time, shared by the title and tutorial."""
import pico2d

from .settings import ROOT


class MusicManager:
    TRACKS = {
        'title': ROOT / 'sound/sound/title_bgm/placidplace-fantasy-lucid-forestpart-two-49992.mp3',
        'tutorial': ROOT / 'sound/sound/bgm/stage_1.mp3',
    }

    def __init__(self):
        self.tracks = {}
        self.current = None
        self.volume = 80

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
        track = self.tracks.get(self.current)
        if track is not None:
            track.stop()
        self.current = None
        self.tracks.clear()
