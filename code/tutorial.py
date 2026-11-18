"""Input-driven Korean lessons and contextual interaction hints."""
import math
import pico2d
from .settings import ROOT, IMAGE_ROOT, SCREEN_WIDTH, SCREEN_HEIGHT


ABILITY_TEXT = {
    'blue': ('파랑 · 물의 상태', '파랑을 주면 물이 액체가 되어 통과할 수 있어요.',
             '좌클릭으로 회수하면 회색 고체가 되어 밟을 수 있어요.'),
    'green': ('초록 · 생장', '초록을 주면 시든 식물과 덩굴이 자라 길을 만들어요.',
              '색을 회수하면 길이 사라져요. 안전한 곳에서 옮겨 보세요.'),
    'yellow': ('노랑 · 빛', '노랑은 등불과 고대 문양에 빛을 밝혀요.',
               '빛으로 숨은 길을 드러내고 연결된 봉인을 열 수 있어요.'),
}


class Tutorial:
    def __init__(self):
        ui = IMAGE_ROOT / 'ui/Controllers and Keyboard/Controllers and Keyboard'
        self.keyboard = pico2d.load_image(str(ui / 'kb_light_all.png'))
        self.mouse = pico2d.load_image(str(ui / 'mouse.png'))
        self.cursor = pico2d.load_image(str(ui / 'cursors.png'))
        self.panel_bg = pico2d.load_image(str(IMAGE_ROOT / 'ui/tutorial_panel.png'))
        font = ROOT / 'fonts/Galmuri-v2.40.4/Galmuri11.ttf'
        self.font = pico2d.load_font(str(font), 22)
        self.small = pico2d.load_font(str(font), 16)
        self.reset()

    def reset(self):
        self.time = 0.0
        self.pressed = set()
        self.counts = {pico2d.SDLK_a: 0, pico2d.SDLK_d: 0}
        self.moved = self.jumped = self.fell = False
        self.mouse_pos = None
        self.seen_transfers = set()
        self.transfer_serial = 0
        self.message = None
        self.complete = False
        self.paused = False
        self.drop_serial = 0

    @property
    def lesson(self):
        if not self.moved:
            return 'move'
        if not self.jumped:
            return 'jump'
        if not self.fell:
            return 'fall'
        return 'color'

    def handle_event(self, event, player):
        if event.type == pico2d.SDL_WINDOWEVENT:
            if event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
                self.pressed.clear()
                self.mouse_pos = None
        elif event.type in (pico2d.SDL_MOUSEMOTION, pico2d.SDL_MOUSEBUTTONDOWN,
                            pico2d.SDL_MOUSEBUTTONUP):
            self.mouse_pos = (event.x, SCREEN_HEIGHT - event.y)
        elif event.type == pico2d.SDL_KEYUP:
            self.pressed.discard(event.key)
        elif event.type == pico2d.SDL_KEYDOWN:
            fresh = event.key not in self.pressed and not getattr(event, 'repeat', False)
            self.pressed.add(event.key)
            if event.key == pico2d.SDLK_r:
                self.reset()
                return
            if event.key == pico2d.SDLK_ESCAPE and fresh:
                self.paused = not self.paused
                player.keys.clear()
            if self.paused:
                return
            if not fresh:
                return
            if event.key == pico2d.SDLK_RETURN and self.message:
                self.message = None
                return
            if self.lesson == 'move' and event.key in self.counts:
                self.counts[event.key] += 1
                self.moved = all(count >= 2 for count in self.counts.values())
            elif self.lesson == 'jump' and event.key == pico2d.SDLK_SPACE and player.grounded:
                self.jumped = True

    def update(self, dt, level, player, colors):
        if self.paused:
            return
        self.time += dt
        if player.drop_serial != self.drop_serial:
            self.drop_serial = player.drop_serial
            self.fell = True
        if not getattr(level, 'show_color_messages', getattr(level, 'gimmicks_enabled', True)):
            self.message = None
            return
        if colors.transfer_serial != self.transfer_serial:
            self.transfer_serial = colors.transfer_serial
            if colors.last_transfer and colors.last_transfer not in self.seen_transfers:
                color, action = colors.last_transfer
                self.seen_transfers.add(colors.last_transfer)
                if action == 'reclaim':
                    self.message = ('색을 회수했어요', '물이 다시 굳었어요. 이제 발판으로 사용할 수 있어요.',
                                    '다음 물에 색을 옮기려면 가까이에서 좌클릭하세요.')
                else:
                    self.message = ABILITY_TEXT[color]
        if level.at_end(player) and not self.complete:
            self.complete = True

    def panel(self, left, bottom, right, top):
        self.panel_bg.draw((left + right) / 2, (bottom + top) / 2,
                           right - left, top - bottom)
        pico2d.draw_rectangle(left, bottom, right, top, 142, 132, 167)

    def key_icon(self, col, row, x, y, width=40, cells=1):
        # Sheet cells are 16px. Down-state variants sit in the next column.
        down = int(self.time * 3) % 2
        self.keyboard.clip_draw((col + down * cells) * 16, self.keyboard.h - (row + 1) * 16,
                                cells * 16, 16, x, y - down * 3, width, 40)

    def draw(self, level, player, colors, camera_x, camera_y=0):
        x = max(64, min(SCREEN_WIDTH - 64, player.x - camera_x))
        y = min(SCREEN_HEIGHT - 34, player.top - camera_y + 16 + math.sin(self.time * 4) * 2)
        if self.lesson == 'move' and not self.message:
            self.key_icon(0, 0, x - 32, y + 12)
            self.key_icon(0, 3, x + 32, y + 12)
        elif self.lesson == 'jump' and not self.message:
            self.key_icon(8, 8, x, y + 12, 64)
        elif self.lesson == 'fall' and player.drop_platforms and not self.message:
            self.key_icon(0, 18, x, y + 12)
        if self.mouse_pos:
            mx, my = self.mouse_pos
            valid = (0 <= mx < SCREEN_WIDTH and 0 <= my < SCREEN_HEIGHT
                     and colors.target_at(mx + camera_x, my + camera_y, level, player))
            if valid:
                pulse = .45 + .55 * (.5 + .5 * math.sin(self.time * 10))
                self.mouse.opacify(pulse)
                self.mouse.clip_draw(0, self.mouse.h - 16, 16, 16, mx + 30, my + 24, 40, 40)
                self.cursor.opacify(pulse)
                self.cursor.clip_draw(0, self.cursor.h - 16, 16, 16, mx + 5, my - 7, 32, 32)
        if self.message and getattr(level, 'show_color_messages', getattr(level, 'gimmicks_enabled', True)):
            self.panel(184, 214, 968, 434)
            self.font.draw(216, 394, self.message[0], (241, 221, 163))
            for index, line in enumerate(self.message[1:]):
                self.small.draw(216, 346 - index * 30, line, (242, 235, 247))
            if int(self.time * 2) % 2 == 0:
                self.small.draw(834, 242, '[ ENTER ]', (241, 221, 163))
        if self.paused:
            self.panel(330, 228, 822, 420)
            self.font.draw(480, 370, '일시정지', (242, 232, 255))
            self.small.draw(394, 320, 'ESC : 계속하기     R : 처음부터', (235, 229, 243))
            self.small.draw(394, 278, '게임 종료 : 창 닫기 또는 Alt+F4', (185, 177, 201))
