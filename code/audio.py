"""One looping BGM at a time, shared by the title and tutorial."""
import pico2d

from .settings import ROOT


class MusicManager:
    PACK = ROOT / 'sound/sound/ui_sound/400 Sounds Pack'
    MAGIC = ROOT / 'sound/sound/wav'
    EFFECTS = {
        'step': ((PACK / 'Footsteps/digital/digital_footstep_grass_1.wav',
                  PACK / 'Footsteps/digital/digital_footstep_grass_2.wav'), .4),
        'land': ((PACK / 'Footsteps/digital/digital_footstep_grass_1.wav',), .55),
        'jump': ((PACK / 'Other/whoosh_1.wav',), .2),
        'extract': ((MAGIC / 'mana_01.wav',), .3),
        'give': ((MAGIC / 'enchant_01.wav',), .3),
        'water': ((MAGIC / 'water_cast_01.wav',), .3),
        'freeze': ((MAGIC / 'ice_cast_01.wav',), .25),
        'convert': ((MAGIC / 'mana_01.wav',), .18),
    }
    GAINS = {'title': 1.0, 'tutorial': 0.25}
    CLICK_PATH = ROOT / 'sound/sound/ui_sound/UI_Click_Soft_Wood_V02.wav'
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
        self.effects = {}
        self.effect_gains = {}
        self.effect_counts = {}

    def play_effect(self, name):
        paths, gain = self.EFFECTS[name]
        count = self.effect_counts.get(name, 0)
        path = paths[count % len(paths)]
        self.effect_counts[name] = count + 1
        if path not in self.effects:
            try:
                self.effects[path] = pico2d.load_wav(str(path))
            except OSError:
                self.effects[path] = None
        sound = self.effects[path]
        if sound is not None:
            self.effect_gains[path] = gain
            sound.set_volume(round(self.effects_volume * gain * 128 / 100))
            sound.play()

    def set_effects_volume(self, value):
        self.effects_volume = max(0, min(100, value))
        if self.click_sound is not None:
            self.click_sound.set_volume(round(self.effects_volume * 128 / 100))
        for path, sound in self.effects.items():
            if sound is not None:
                sound.set_volume(round(self.effects_volume * self.effect_gains[path] * 128 / 100))

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
            track.set_volume(round(self.volume * self.GAINS[scene] * 128 / 100))
            track.repeat_play()

    def set_volume(self, value):
        value = max(0, min(100, value))
        if self.volume == value:
            return
        self.volume = value
        track = self.tracks.get(self.current)
        if track is not None:
            track.set_volume(round(value * self.GAINS[self.current] * 128 / 100))

    def close(self):
        if self.click_sound is not None or self.effects:
            pico2d.Mix_HaltChannel(-1)
            self.click_sound = None
            self.effects.clear()
        track = self.tracks.get(self.current)
        if track is not None:
            track.stop()
        self.current = None
        self.tracks.clear()
