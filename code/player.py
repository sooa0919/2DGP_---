import pico2d

from .settings import GROUND_HEIGHT, IMAGE_ROOT, SCREEN_HEIGHT, WORLD_WIDTH


class Player:
    SIZE = 64
    DRAW_SIZE = 96
    SPEED = 240.0
    GRAVITY = 1500.0
    JUMP_SPEED = 560.0
    FAST_FALL_GRAVITY = 3000.0
    ANIMATION_FPS = {"idle": 8.0, "run": 10.0}
    MOVEMENT_KEYS = (pico2d.SDLK_w, pico2d.SDLK_a, pico2d.SDLK_s, pico2d.SDLK_d)

    def __init__(self):
        self.images = {
            state: pico2d.load_image(
                str(IMAGE_ROOT / "character" / state / f"{state}_blue.png")
            )
            for state in ("idle", "run")
        }
        self.x = 200.0
        self.y = GROUND_HEIGHT + self.DRAW_SIZE / 2
        self.keys = set()
        self.state = "idle"
        self.frame = 0.0
        self.facing = 1
        self.velocity_y = 0.0
        self.grounded = True

    def handle_event(self, event):
        if event.type == pico2d.SDL_WINDOWEVENT:
            if event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
                self.keys.clear()
        elif event.type == pico2d.SDL_KEYDOWN and event.key in self.MOVEMENT_KEYS:
            if event.key == pico2d.SDLK_w and event.key not in self.keys and self.grounded:
                self.velocity_y = self.JUMP_SPEED
                self.grounded = False
            self.keys.add(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self.keys.discard(event.key)

    def update(self, dt):
        dx = int(pico2d.SDLK_d in self.keys) - int(pico2d.SDLK_a in self.keys)
        old_x = self.x
        self.x += dx * self.SPEED * dt
        if not self.grounded:
            gravity = (self.FAST_FALL_GRAVITY if pico2d.SDLK_s in self.keys
                       else self.GRAVITY)
            self.y += self.velocity_y * dt - 0.5 * gravity * dt * dt
            self.velocity_y -= gravity * dt
        half = self.DRAW_SIZE / 2
        self.x = max(half, min(self.x, WORLD_WIDTH - half))
        if self.y <= GROUND_HEIGHT + half:
            self.y = GROUND_HEIGHT + half
            self.velocity_y = 0.0
            self.grounded = True
        elif self.y > SCREEN_HEIGHT - half:
            self.y = SCREEN_HEIGHT - half
            self.velocity_y = min(0.0, self.velocity_y)
        if dx:
            self.facing = 1 if dx > 0 else -1
        state = "run" if self.x != old_x or not self.grounded else "idle"
        if state != self.state:
            self.state, self.frame = state, 0.0
        image = self.images[self.state]
        count = (image.w // self.SIZE) * (image.h // self.SIZE)
        self.frame = (self.frame + self.ANIMATION_FPS[self.state] * dt) % count

    def draw(self, camera_x):
        image = self.images[self.state]
        columns = image.w // self.SIZE
        row, column = divmod(int(self.frame), columns)
        # The source sprites face left, so flip them when facing right.
        image.clip_composite_draw(
            column * self.SIZE, image.h - (row + 1) * self.SIZE,
            self.SIZE, self.SIZE, 0, "h" if self.facing > 0 else "",
            round(self.x - camera_x), round(self.y), self.DRAW_SIZE, self.DRAW_SIZE,
        )
