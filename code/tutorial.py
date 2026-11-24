"""Compact controls, color selection and guidance for the new puzzle route."""
import math
import pico2d
from .display import load_pixel_image

from .settings import FONT_PATH, IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT


class Tutorial:
    def __init__(self):
        self.keyboard = load_pixel_image(str(
            IMAGE_ROOT / 'ui/Controllers and Keyboard/Controllers and Keyboard/kb_light_all.png'))
        self.small = pico2d.load_font(str(FONT_PATH), 15)
        self.reset()

    def reset(self):
        self.pressed = set()
        self.mouse_pos = None
        self.paused = False
        self.complete = False
        self.message = None
        self.time = 0.0
        self.moved = False
        self.jumped = False
        self.fell = False
        self.drop_serial = 0

    def handle_event(self, event, player):
        if event.type in (pico2d.SDL_MOUSEMOTION, pico2d.SDL_MOUSEBUTTONDOWN, pico2d.SDL_MOUSEBUTTONUP):
            self.mouse_pos = (event.x, SCREEN_HEIGHT - event.y)
        elif event.type == pico2d.SDL_KEYDOWN:
            if event.key == pico2d.SDLK_r:
                self.reset()
            elif event.key == pico2d.SDLK_SPACE and player.grounded:
                self.jumped = True
        elif event.type == pico2d.SDL_WINDOWEVENT and event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
            self.mouse_pos = None

    def update(self, dt, level, player, colors):
        self.time += dt
        self.moved |= abs(player.x - level.spawn[0]) >= 24
        if player.drop_serial != self.drop_serial:
            self.drop_serial = player.drop_serial
            self.fell = True
        self.complete = level.complete

    def key_icon(self, col, row, x, y, width=40):
        down = int(self.time * 3) % 2
        self.keyboard.clip_draw((col + down) * 16, self.keyboard.h - (row + 1) * 16,
                                16, 16, round(x), round(y - down * 3), width, 40)

    def head_keys(self, player, camera_x, camera_y):
        x = max(44, min(SCREEN_WIDTH - 44, player.x - camera_x))
        size = player.RUN_DRAW_SIZE if player.state == 'run' else (
            player.JUMP_DRAW_SIZE if player.state in ('jump', 'fall') else player.DRAW_SIZE)
        y = min(SCREEN_HEIGHT - 72, player.bottom - camera_y + size + 22 + math.sin(self.time * 4) * 2)
        if not self.moved:
            self.key_icon(0, 0, x - 24, y)
            self.key_icon(0, 3, x + 24, y)
        elif not self.jumped:
            self.key_icon(8, 8, x, y, 64)
        elif not self.fell and player.drop_platforms:
            self.key_icon(0, 18, x, y)

    def draw(self, level, player, colors, camera_x, camera_y=0):
        if not self.complete:
            self.head_keys(player, camera_x, camera_y)
        for index, (color, label, rgb) in enumerate((('blue', '1 파랑', (68, 170, 235)),
                                                     ('green', '2 초록', (75, 195, 110)),
                                                     ('yellow', '3 노랑', (245, 212, 90)))):
            x = SCREEN_WIDTH - 312 + index * 96
            selected = player.color == color
            pico2d.draw_rectangle(x, SCREEN_HEIGHT - 48, x + 88, SCREEN_HEIGHT - 15,
                                  *(rgb if selected else (61, 66, 70)), filled=True)
            self.small.draw(x + 10, SCREEN_HEIGHT - 31, label, (245, 245, 240))
        self.small.draw(28, SCREEN_HEIGHT - 30,
                        colors.notice or ('보유 색 없음' if player.color is None else '보유 색: ' +
                        {'blue': '파랑', 'green': '초록', 'yellow': '노랑'}[player.color]), (245, 245, 240))
        if self.mouse_pos:
            x, y = self.mouse_pos
            target = colors.target_at(x + camera_x, y + camera_y, level, player)
            if target:
                self.small.draw(min(x + 18, SCREEN_WIDTH - 130), min(y + 22, SCREEN_HEIGHT - 65),
                                '좌클릭 부여/회수', (255, 245, 195))
