"""Title menus using the two rows of the supplied button sprite sheet."""

import pico2d

from .settings import IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH


class TitleScreen:
    # Source rectangles use top-left coordinates. Each column has two states.
    COLUMNS = {
        'start': (45, 440),
        'settings': (455, 730),
        'quit': (740, 1025),
        'new': (1035, 1380),
        'load': (1385, 1740),
    }
    SCALE = 0.6
    LEFT = 82
    FIRST_Y = 370
    SPACING = 110
    FRAME_HEIGHT = 175

    def __init__(self):
        self.background = pico2d.load_image(str(IMAGE_ROOT / 'ui/title.png'))
        self.sheet = pico2d.load_image(str(IMAGE_ROOT / 'ui/title_select.webp'))
        self.menu = 'main'
        self.mouse = None

    @property
    def buttons(self):
        return ('start', 'settings', 'quit') if self.menu == 'main' else ('new', 'load')

    def bounds(self, name):
        index = self.buttons.index(name)
        left, right = self.COLUMNS[name]
        width = (right - left) * self.SCALE
        height = self.FRAME_HEIGHT * self.SCALE
        y = self.FIRST_Y - index * self.SPACING
        return self.LEFT, y - height / 2, self.LEFT + width, y + height / 2

    @property
    def hovered(self):
        if self.mouse is None:
            return None
        x, y = self.mouse
        for name in self.buttons:
            left, bottom, right, top = self.bounds(name)
            if left <= x < right and bottom <= y < top:
                return name
        return None

    def handle_event(self, event):
        if event.type == pico2d.SDL_KEYDOWN and event.key == pico2d.SDLK_ESCAPE:
            self.menu = 'main'
        elif event.type in (pico2d.SDL_MOUSEMOTION, pico2d.SDL_MOUSEBUTTONDOWN,
                            pico2d.SDL_MOUSEBUTTONUP):
            # SDL already converts fullscreen mouse events to logical coordinates.
            self.mouse = (event.x, SCREEN_HEIGHT - event.y)
            if (event.type == pico2d.SDL_MOUSEBUTTONDOWN
                    and event.button == pico2d.SDL_BUTTON_LEFT):
                selected = self.hovered
                if selected == 'start':
                    self.menu = 'start'
                elif selected in ('new', 'quit'):
                    return selected
        return None

    def draw(self):
        self.background.draw(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                             SCREEN_WIDTH, SCREEN_HEIGHT)
        hovered = self.hovered
        for name in self.buttons:
            left, right = self.COLUMNS[name]
            source_top = 437 if name == hovered else 230
            x1, y1, x2, y2 = self.bounds(name)
            self.sheet.clip_draw(left, self.sheet.h - source_top - self.FRAME_HEIGHT,
                                 right - left, self.FRAME_HEIGHT,
                                 (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1)
