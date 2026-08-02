import math
import random
import pygame as pg

from config import SCREEN_WIDTH, SCREEN_HEIGHT
from textures import get_weapon_image

_bullet_cache = {}


def _get_bullet_surface(target_h):
    target_h = max(4, int(target_h))
    if target_h not in _bullet_cache:
        if len(_bullet_cache) > 64:
            _bullet_cache.clear()
        img = get_weapon_image("bullet")
        if img is None:
            _bullet_cache[target_h] = None
        else:
            rect = img.get_bounding_rect(min_alpha=8)
            if rect.width <= 0 or rect.height <= 0:
                _bullet_cache[target_h] = None
            else:
                b = img.subsurface(rect)
                scale = target_h / b.get_height()
                _bullet_cache[target_h] = pg.transform.smoothscale(
                    b, (max(1, int(b.get_width() * scale)), target_h)
                )
    return _bullet_cache[target_h]


class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 40.0
        self.life = 0.6
        self.alive = True
        self.trail = []
        self.hit_pos = None
        self.hit_target = None

    def update(self, dt, game_map, targets=None):
        if not self.alive:
            return False
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return False

        dx = math.cos(self.angle) * self.speed * dt
        dy = math.sin(self.angle) * self.speed * dt
        nx = self.x + dx
        ny = self.y + dy

        if targets:
            for t in targets:
                if not t.alive:
                    continue
                if abs(self.x - t.x) < 0.6 and abs(self.y - t.y) < 0.6:
                    if t.hit(22.5):
                        self.alive = False
                        self.hit_pos = (self.x, self.y)
                        self.hit_target = t
                        return False

        self.trail.append((int(self.x * 6), int(self.y * 6)))
        if len(self.trail) > 15:
            self.trail.pop(0)

        if game_map.is_wall(nx, ny):
            self.alive = False
            self.hit_pos = (self.x, self.y)
            return False

        self.x = nx
        self.y = ny
        return True

    def draw(self, screen, px, py, pdx, pdy, fov):
        if not self.alive and not self.hit_pos:
            return

        pos = self.hit_pos if self.hit_pos else (self.x, self.y)
        dx = pos[0] - px
        dy = pos[1] - py
        dist = math.hypot(dx, dy)
        if dist < 0.3:
            return

        angle_to = math.atan2(dy, dx)
        player_angle = math.atan2(pdy, pdx)
        diff = angle_to - player_angle
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi

        if abs(diff) > math.radians(fov / 2):
            return

        half_fov = math.radians(fov / 2)
        screen_x = int((diff / half_fov) * (SCREEN_WIDTH // 2) + SCREEN_WIDTH // 2)
        screen_h = int(SCREEN_HEIGHT / dist * 0.15)

        if 0 <= screen_x < SCREEN_WIDTH:
            is_hit = not self.alive and self.hit_pos
            size = int(screen_h * 0.5) if is_hit else max(6, screen_h // 2)
            bullet_surf = _get_bullet_surface(size)
            if bullet_surf is not None:
                screen.blit(bullet_surf, (screen_x - bullet_surf.get_width() // 2, SCREEN_HEIGHT // 2 - bullet_surf.get_height() // 2))
            else:
                c = (255, 120, 50) if is_hit else (255, 220, 80)
                pg.draw.rect(screen, c, (screen_x - 1, SCREEN_HEIGHT // 2 - size // 2, 3, max(1, size)))


class Shell:
    def __init__(self, x, y):
        self.x = x
        self.y = y - 40
        self.vx = random.uniform(-30, -10)
        self.vy = random.uniform(-80, -40)
        self.life = 0.8
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-500, 500)

    def update(self, dt):
        self.life -= dt
        self.vy += 400 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rot_speed * dt
        return self.life > 0

    def draw(self, screen):
        if not (0 <= self.x < 1920 and 0 <= self.y < 1080):
            return
        w, h = 8, 4
        cos_a = math.cos(math.radians(self.rotation))
        sin_a = math.sin(math.radians(self.rotation))
        cx, cy = self.x, self.y
        pts = [
            (cx + (-w // 2) * cos_a - (-h // 2) * sin_a,
             cy + (-w // 2) * sin_a + (-h // 2) * cos_a),
            (cx + (w // 2) * cos_a - (-h // 2) * sin_a,
             cy + (w // 2) * sin_a + (-h // 2) * cos_a),
            (cx + (w // 2) * cos_a - (h // 2) * sin_a,
             cy + (w // 2) * sin_a + (h // 2) * cos_a),
            (cx + (-w // 2) * cos_a - (h // 2) * sin_a,
             cy + (-w // 2) * sin_a + (h // 2) * cos_a),
        ]
        pg.draw.polygon(screen, (180, 140, 60), pts)
        pg.draw.polygon(screen, (120, 90, 40), pts, 1)


class MuzzleFlash:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 0.08
        self.max_life = 0.08

    def update(self, dt):
        self.life -= dt
        return self.life > 0

    def draw(self, screen):
        progress = 1 - (self.life / self.max_life)
        radius = int(20 * (1 - progress * 0.5))
        for r in range(radius, 0, -2):
            a_max = 255 * (1 - progress)
            a = int(a_max * (1 - r / radius))
            c = (255, 255 - int(r * 3), 200 - int(r * 2))
            pg.draw.circle(screen, c, (self.x, self.y), r)
