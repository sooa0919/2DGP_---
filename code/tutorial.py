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
        self.message_time = 0.0
        self.complete = False
        self.paused = False

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
            if self.lesson == 'move' and event.key in self.counts:
                self.counts[event.key] += 1
                self.moved = all(count >= 2 for count in self.counts.values())
            elif self.lesson == 'jump' and event.key == pico2d.SDLK_SPACE and player.grounded:
                self.jumped = True
            elif self.lesson == 'fall' and event.key == pico2d.SDLK_s and not player.grounded:
                self.fell = True
            elif event.key in (pico2d.SDLK_RETURN, pico2d.SDLK_SPACE) and self.message:
                self.message = None

    def update(self, dt, level, player, colors):
        if self.paused:
            return
        self.time += dt
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
                self.message_time = 12.0
        if self.message:
            self.message_time -= dt
            if self.message_time <= 0:
                self.message = None
        if level.at_end(player) and not self.complete:
            self.complete = True
            self.message = ('사원 탐색 완료', '이동과 색 옮기기를 연습했어요!',
                            'R : 처음부터 다시 연습     ESC : 일시정지')
            self.message_time = 9999

    @staticmethod
    def panel(left, bottom, right, top):
        pico2d.draw_rectangle(left, bottom, right, top, 26, 25, 39, filled=True)
        pico2d.draw_rectangle(left, bottom, right, top, 142, 132, 167)

    def key_icon(self, col, row, x, y, width=40, cells=1):
        # Sheet cells are 16px. Down-state variants sit in the next column.
        down = int(self.time * 3) % 2
        self.keyboard.clip_draw((col + down * cells) * 16, self.keyboard.h - (row + 1) * 16,
                                cells * 16, 16, x, y - down * 3, width, 40)

    def draw(self, level, player, colors, camera_x):
        zone = next(label for start, label in reversed(level.zones) if player.x >= start)
        self.panel(20, SCREEN_HEIGHT - 64, 440, SCREEN_HEIGHT - 18)
        self.font.draw(36, SCREEN_HEIGHT - 40, '무너진 사원  /  ' + zone, (229, 222, 242))
        self.small.draw(24, 22, 'A/D 이동   SPACE 점프   S 급강하   좌클릭 색 옮기기   R 재시작   ESC 일시정지',
                        (219, 211, 229))
        x = max(210, min(SCREEN_WIDTH - 210, player.x - camera_x))
        y = min(SCREEN_HEIGHT - 140, player.top + 86 + math.sin(self.time * 4) * 4)
        if self.lesson == 'move':
            self.panel(x - 194, y - 45, x + 194, y + 42)
            self.key_icon(0, 0, x - 32, y + 12)
            self.key_icon(0, 3, x + 32, y + 12)
            self.small.draw(x - 178, y - 24,
                            f'A와 D를 각각 두 번 눌러 이동해요 ({min(self.counts[pico2d.SDLK_a], 2)}/2 · {min(self.counts[pico2d.SDLK_d], 2)}/2)',
                            (245, 238, 250))
        elif self.lesson == 'jump':
            self.panel(x - 145, y - 45, x + 145, y + 42)
            self.key_icon(8, 8, x, y + 12, 96, 2)
            self.small.draw(x - 115, y - 24, 'SPACE를 눌러 점프해 보세요', (245, 238, 250))
        elif self.lesson == 'fall':
            self.panel(x - 164, y - 45, x + 164, y + 42)
            self.key_icon(0, 18, x, y + 12)
            self.small.draw(x - 146, y - 24, '점프한 뒤 S를 눌러 빨리 내려와요', (245, 238, 250))
        elif player.x < 1728 and not self.message:
            self.panel(310, 80, 842, 130)
            text = '가까운 물에 좌클릭 : 파랑 주기 / 회수하기'
            self.small.draw(330, 105, text, (235, 229, 245))
        elif 1728 <= player.x < 3680 and not self.message:
            lines = ABILITY_TEXT['green' if player.x < 3072 else 'yellow']
            self.panel(210, 74, 942, 164)
            self.font.draw(230, 138, lines[0], (222, 211, 244))
            self.small.draw(230, 106, lines[1], (237, 232, 244))
            self.small.draw(230, 84, '장치 배치 전 구간 · 지금은 사원 지형을 따라 이동하세요.', (182, 176, 194))
        if self.mouse_pos:
            mx, my = self.mouse_pos
            valid = (0 <= mx < SCREEN_WIDTH and 0 <= my < SCREEN_HEIGHT
                     and colors.target_at(mx + camera_x, my, level, player))
            if valid:
                pulse = .45 + .55 * (.5 + .5 * math.sin(self.time * 10))
                self.mouse.opacify(pulse)
                self.mouse.clip_draw(0, self.mouse.h - 16, 16, 16, mx + 30, my + 24, 40, 40)
                self.cursor.opacify(pulse)
                self.cursor.clip_draw(0, self.cursor.h - 16, 16, 16, mx + 5, my - 7, 32, 32)
                self.small.draw(min(mx + 50, SCREEN_WIDTH - 160), max(42, my + 24),
                                '색 회수' if valid.has_blue else '색 부여', (241, 234, 255))
        if self.message:
            self.panel(184, 68, 968, 208)
            self.font.draw(208, 179, self.message[0], (241, 221, 163))
            for index, line in enumerate(self.message[1:]):
                self.small.draw(208, 145 - index * 26, line, (242, 235, 247))
            self.small.draw(208, 88, 'ENTER로 닫기', (174, 167, 191))
        if self.paused:
            self.panel(330, 228, 822, 420)
            self.font.draw(480, 370, '일시정지', (242, 232, 255))
            self.small.draw(394, 320, 'ESC : 계속하기     R : 처음부터', (235, 229, 243))
            self.small.draw(394, 278, '게임 종료 : 창 닫기 또는 Alt+F4', (185, 177, 201))
