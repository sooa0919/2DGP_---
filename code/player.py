import pico2d

from .settings import GROUND_HEIGHT, IMAGE_ROOT, SCREEN_HEIGHT, WORLD_WIDTH


class Player:
    SIZE = 64
    DRAW_SIZE = 72
    RUN_DRAW_SIZE = 80
    JUMP_DRAW_SIZE = 88
    # Opaque lower edge of each supplied run frame, in source pixels.
    RUN_FOOT_ROWS = (60, 64, 64, 55, 52, 60, 64, 64, 55, 52)
    JUMP_FOOT_ROWS = (60, 59, 58, 58)
    # Opaque body/head envelope in the 64px source: x=6..58, y=8..64.
    # The run pose leans forward; include its head without using the full frame.
    HALF_WIDTH = 26 * DRAW_SIZE / SIZE
    FOOT_HALF_WIDTH = 7 * DRAW_SIZE / SIZE
    TOP_OFFSET = 24 * DRAW_SIZE / SIZE
    FOOT_OFFSET = DRAW_SIZE / 2
    SPEED = 240.0
    GRAVITY = 1500.0
    JUMP_SPEED = 560.0
    ANIMATION_FPS = {"idle": 8.0, "run": 10.0, "jump": 8.0, "fall": 8.0}
    MOVEMENT_KEYS = (pico2d.SDLK_SPACE, pico2d.SDLK_a, pico2d.SDLK_s, pico2d.SDLK_d)

    def __init__(self, level=None):
        self.level = level
        self.images = {
            state: pico2d.load_image(
                str(IMAGE_ROOT / "character" / state / f"{state}_blue.png")
            )
            for state in ("idle", "run", "jump")
        }
        self.gray_images = {
            "idle": pico2d.load_image(str(IMAGE_ROOT / "character" / "idle" / "idle_gray.png")),
            "run": pico2d.load_image(str(IMAGE_ROOT / "character" / "run" / "run_grey.png")),
            "jump": pico2d.load_image(str(IMAGE_ROOT / "character" / "jump" / "jump_grey.png")),
        }
        self.images["fall"] = self.images["jump"]
        self.gray_images["fall"] = self.gray_images["jump"]
        self.has_blue = True
        self.x = 200.0
        self.y = GROUND_HEIGHT + self.DRAW_SIZE / 2
        self.keys = set()
        self.state = "idle"
        self.frame = 0.0
        self.facing = 1
        self.velocity_y = 0.0
        self.grounded = True
        self.ignored_platforms = []
        self.drop_serial = 0

    def handle_event(self, event):
        if event.type == pico2d.SDL_WINDOWEVENT:
            if event.event == pico2d.SDL_WINDOWEVENT_FOCUS_LOST:
                self.keys.clear()
        elif event.type == pico2d.SDL_KEYDOWN and event.key in self.MOVEMENT_KEYS:
            if event.key == pico2d.SDLK_s and event.key not in self.keys:
                self.drop_through()
            if event.key == pico2d.SDLK_SPACE and event.key not in self.keys and self.grounded:
                self.velocity_y = self.JUMP_SPEED
                self.grounded = False
            self.keys.add(event.key)
        elif event.type == pico2d.SDL_KEYUP:
            self.keys.discard(event.key)

    def update(self, dt):
        dx = int(pico2d.SDLK_d in self.keys) - int(pico2d.SDLK_a in self.keys)
        if self.level is not None:
            remaining = dt
            while remaining > 1e-9:
                step = min(remaining, 1 / 120)
                self._move_on_platforms(step, dx)
                remaining -= step
            self._animate(dt, dx)
            return
        self.x += dx * self.SPEED * dt
        if not self.grounded:
            gravity = self.GRAVITY
            self.y += self.velocity_y * dt - 0.5 * gravity * dt * dt
            self.velocity_y -= gravity * dt
        self.x = max(self.HALF_WIDTH, min(self.x, WORLD_WIDTH - self.HALF_WIDTH))
        if self.bottom <= GROUND_HEIGHT:
            self.y = GROUND_HEIGHT + self.FOOT_OFFSET
            self.velocity_y = 0.0
            self.grounded = True
        elif self.top > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.TOP_OFFSET
            self.velocity_y = min(0.0, self.velocity_y)
        self._animate(dt, dx)

    def enter_level(self, level):
        self.level = level
        level.reset_water()
        self.has_blue = True
        self.x, floor = level.spawn
        self.y = floor + self.DRAW_SIZE / 2
        self.velocity_y = 0.0
        self.grounded = True
        self.state, self.frame = "idle", 0.0
        self.keys.clear()
        self.ignored_platforms.clear()
        self.drop_serial = 0

    @property
    def drop_platforms(self):
        if self.level is None or not self.grounded:
            return []
        return [p for p in self.level.collision_platforms()
                if p.one_way and abs(self.bottom - p.top) < .1
                and self.x + self.FOOT_HALF_WIDTH > p.left
                and self.x - self.FOOT_HALF_WIDTH < p.right]

    def drop_through(self):
        supports = self.drop_platforms
        if not supports:
            return
        if any(not p.one_way and abs(self.bottom - p.top) < .1
               and self.x + self.FOOT_HALF_WIDTH > p.left
               and self.x - self.FOOT_HALF_WIDTH < p.right
               for p in self.level.collision_platforms()):
            return
        self.ignored_platforms = supports
        self.grounded = False
        self.velocity_y = min(self.velocity_y, -40.0)
        self.drop_serial += 1

    @property
    def in_water(self):
        return self.level is not None and any(
            pool.has_blue and self.right > pool.left and self.left < pool.right
            and self.bottom < pool.top and self.top > pool.bottom
            for pool in self.level.water)

    @property
    def left(self):
        return self.x - self.HALF_WIDTH

    @property
    def right(self):
        return self.x + self.HALF_WIDTH

    @property
    def bottom(self):
        return self.y - self.FOOT_OFFSET

    @property
    def top(self):
        return self.y + self.TOP_OFFSET

    def _move_on_platforms(self, dt, dx):
        self.ignored_platforms = [p for p in self.ignored_platforms
                                 if self.top >= p.bottom]
        solids = [p for p in self.level.collision_platforms()
                  if p not in self.ignored_platforms]
        old_x = self.x
        speed = self.SPEED * (0.7 if self.in_water else 1.0)
        self.x = max(self.HALF_WIDTH, min(self.x + dx * speed * dt, self.level.width - self.HALF_WIDTH))
        for p in solids:
            if p.one_way:
                continue
            if self.top <= p.bottom + 0.01 or self.bottom >= p.top - 0.01:
                continue
            if self.right > p.left and self.left < p.right:
                if dx > 0 and old_x + self.HALF_WIDTH <= p.left + 0.01:
                    self.x = min(self.x, p.left - self.HALF_WIDTH)
                elif dx < 0 and old_x - self.HALF_WIDTH >= p.right - 0.01:
                    self.x = max(self.x, p.right + self.HALF_WIDTH)
        old_bottom, old_top = self.bottom, self.top
        gravity = self.GRAVITY
        self.y += self.velocity_y * dt - gravity * dt * dt / 2
        self.velocity_y -= gravity * dt
        self.grounded = False
        for p in solids:
            if self.right <= p.left or self.left >= p.right:
                continue
            if self.velocity_y <= 0 and old_bottom >= p.top - 0.01 and self.bottom <= p.top:
                if self.x + self.FOOT_HALF_WIDTH > p.left and self.x - self.FOOT_HALF_WIDTH < p.right:
                    self.y = p.top + self.FOOT_OFFSET
                    self.velocity_y = 0.0
                    self.grounded = True
            elif not p.one_way and self.velocity_y > 0 and old_top <= p.bottom + 0.01 and self.top >= p.bottom:
                self.y = p.bottom - self.TOP_OFFSET
                self.velocity_y = 0.0
        world_height = getattr(self.level, 'height', SCREEN_HEIGHT)
        if self.top > world_height:
            self.y = world_height - self.TOP_OFFSET
            self.velocity_y = min(0.0, self.velocity_y)
        if self.top < -96:
            held_keys = self.keys.copy()
            self.enter_level(self.level)
            self.keys = held_keys

    def _animate(self, dt, dx):
        if dx:
            self.facing = 1 if dx > 0 else -1
        state = ("run" if dx else "idle") if self.grounded else (
            "jump" if self.velocity_y > 0 else "fall")
        image = self.current_images[state]
        count = (image.w // self.SIZE) * (image.h // self.SIZE)
        start = max(0, count - 2) if state == "fall" else 0
        end = max(1, count - 2) if state == "jump" else count
        if state != self.state:
            self.state, self.frame = state, float(start)
        self.frame = start + (self.frame - start + self.ANIMATION_FPS[state] * dt) % (end - start)

    def draw(self, camera_x, camera_y=0):
        image = self.current_images[self.state]
        columns = image.w // self.SIZE
        row, column = divmod(int(self.frame), columns)
        # Run and jump sprites face right; idle sprites face left.
        flip = (self.facing > 0) if self.state == "idle" else (self.facing < 0)
        draw_size = (self.RUN_DRAW_SIZE if self.state == "run" else
                     self.JUMP_DRAW_SIZE if self.state in ("jump", "fall") else self.DRAW_SIZE)
        foot_rows = self.RUN_FOOT_ROWS if self.state == "run" else (
            self.JUMP_FOOT_ROWS if self.state in ("jump", "fall") else (self.SIZE,))
        foot_row = foot_rows[int(self.frame) % len(foot_rows)]
        draw_y = self.bottom + draw_size / 2 - (self.SIZE - foot_row) * draw_size / self.SIZE
        image.clip_composite_draw(
            column * self.SIZE, image.h - (row + 1) * self.SIZE,
            self.SIZE, self.SIZE, 0, "h" if flip else "",
            round(self.x - camera_x), round(draw_y - camera_y), draw_size, draw_size,
        )

    @property
    def current_images(self):
        return self.images if self.has_blue else self.gray_images

    def resolve_solid_water(self, pool):
        if (self.right > pool.left and self.left < pool.right
                and self.bottom < pool.top and self.top > pool.bottom):
            if getattr(pool, 'is_waterfall', False):
                # Push sideways out of a refrozen wall, never onto its ceiling.
                self.x = (pool.left - self.HALF_WIDTH if self.x < (pool.left + pool.right) / 2
                          else pool.right + self.HALF_WIDTH)
                return
            self.y = pool.top + self.FOOT_OFFSET
            self.velocity_y = 0.0
            self.grounded = True
