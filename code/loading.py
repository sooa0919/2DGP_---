"""Timed title fade, animated light-orb loading screen, and play fade-in."""
import json

import pico2d

from .settings import FONT_PATH, IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH


class LoadingScreen:
    FADE_OUT = 0.6
    FADE_IN = 0.8
    TEXT = 'loading..'
    LETTER_TIME = 0.12
    TEXT_HOLD = 0.36
    LOOPS = 2
    CYCLE = len(TEXT) * LETTER_TIME + TEXT_HOLD
    IMAGE_SIZE = 160

    def __init__(self):
        ui = IMAGE_ROOT / 'ui'
        self.sheet = pico2d.load_image(str(ui / 'loading_frames.png'))
        self.black = pico2d.load_image(str(ui / 'fade_black.png'))
        self.frames = json.loads((ui / 'loading_frames.json').read_text(encoding='utf-8'))
        self.font = pico2d.load_font(str(FONT_PATH), 24)
        self.phase = 'out'
        self.time = 0.0
        self.ready = False
        self.presented = False

    @property
    def needs_level(self):
        return self.phase == 'loading' and self.presented and not self.ready

    @property
    def done(self):
        return self.phase == 'done'

    @property
    def text(self):
        count = min(len(self.TEXT), int((self.time % self.CYCLE) / self.LETTER_TIME) + 1)
        return self.TEXT[:count]

    def update(self, dt):
        self.time += dt
        if self.phase == 'out' and self.time >= self.FADE_OUT:
            self.phase, self.time = 'loading', 0.0
        elif self.phase == 'loading' and self.ready and self.time >= self.CYCLE * self.LOOPS:
            self.phase, self.time = 'in', 0.0
        elif self.phase == 'in' and self.time >= self.FADE_IN:
            self.phase, self.time = 'done', 0.0

    def draw(self):
        opacity = 1.0
        if self.phase == 'out':
            opacity = min(1.0, self.time / self.FADE_OUT)
        elif self.phase == 'in':
            opacity = max(0.0, 1.0 - self.time / self.FADE_IN)
        elif self.done:
            return
        self.black.opacify(opacity)
        self.black.draw(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
        if self.phase != 'loading':
            return
        self.presented = True
        durations = self.frames['durations']
        remaining = round(self.time % round(sum(durations), 9), 9)
        frame = 0
        for index, duration in enumerate(durations):
            frame = index
            if remaining < duration - 1e-9:
                break
            remaining -= duration
        width, height = self.frames['width'], self.frames['height']
        scale = self.IMAGE_SIZE / max(width, height)
        self.sheet.clip_draw(frame * width, 0, width, height,
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                             width * scale, height * scale)
        # Keep the text's left edge fixed while typing, centered as a complete word.
        self.font.draw(SCREEN_WIDTH / 2 - 44, SCREEN_HEIGHT / 2 - 110,
                       self.text, (240, 240, 230))
