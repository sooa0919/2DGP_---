"""Title menus using the supplied title artwork and normal/hover buttons."""

import pico2d

from .settings import IMAGE_ROOT, SCREEN_HEIGHT, SCREEN_WIDTH


class TitleScreen:
    # Source rectangles use top-left coordinates. Each column has two states.
    COLUMNS = {
        'start': (95, 525),
        'settings': (565, 870),
        'quit': (910, 1230),
        'new': (1265, 1650),
        'load': (1670, 2100),
    }
    SCALE = 0.5
    LEFT = 82
    FIRST_Y = 370
    SPACING = 96
    FRAME_HEIGHT = 170
    NORMAL_TOP = 210
    NORMAL_HEIGHT = 120
    HOVER_TOP = 330

    def __init__(self):
        ui = IMAGE_ROOT / 'ui'
        self.background = pico2d.load_image(str(ui / 'title.png'))
        self.sheet = pico2d.load_image(str(ui / 'title_button.png'))
        self.menu = 'main'
        self.mouse = None

    def update(self, dt):
        pass

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
                elif selected in ('new', 'quit', 'settings'):
                    return selected
        return None

    def draw(self):
        self.background.draw(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, SCREEN_WIDTH, SCREEN_HEIGHT)
        hovered = self.hovered
        for name in self.buttons:
            left, right = self.COLUMNS[name]
            source_top = self.HOVER_TOP if name == hovered else self.NORMAL_TOP
            source_height = self.FRAME_HEIGHT if name == hovered else self.NORMAL_HEIGHT
            x1, y1, x2, y2 = self.bounds(name)
            height = source_height * self.SCALE
            self.sheet.clip_draw(left, self.sheet.h - source_top - source_height,
                                 right - left, source_height,
                                 (x1 + x2) / 2, y2 - height / 2, x2 - x1, height)
