import math
import random
import pygame as pg
from textures import get_weapon_image

_weapon_cache = {}

def _get_weapon_surface(name, target_w, target_h):
    key = (name, target_w, target_h)
    if key not in _weapon_cache:
        img = get_weapon_image(name)
        if img is None:
            _weapon_cache[key] = None
        else:
            rect = img.get_bounding_rect(min_alpha=8)
            if rect.width <= 0 or rect.height <= 0:
                _weapon_cache[key] = None
            else:
                weapon = img.subsurface(rect)
                scale = min(target_w / weapon.get_width(), target_h / weapon.get_height())
                tw = max(1, int(weapon.get_width() * scale))
                th = max(1, int(weapon.get_height() * scale))
                _weapon_cache[key] = pg.transform.smoothscale(weapon, (tw, th))
    return _weapon_cache[key]


class BaseWeapon:
    def __init__(self):
        self.damage = 0
        self.fire_rate = 0.1
        self.mag_size = 0
        self.ammo = 0
        self.reserve = 0
        self.reload_time = 0
        self.reloading = False
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0
        self.kickback = 0.0
        self.recoil_angle = 0.0
        self.bob_offset = 0.0
        self.bob_phase = 0.0
        self.shells = []
        self.muzzle_flash = None
        self.shooting = False
        self.is_melee = False
        self.is_throwable = False

    def shoot(self):
        if self.reloading or self.fire_cooldown > 0 or self.ammo <= 0:
            if self.ammo <= 0 and not self.reloading:
                self.start_reload()
            return False
        self.ammo -= 1
        self.fire_cooldown = self.fire_rate
        self.kickback = 3.0
        self.recoil_angle = min(self.recoil_angle + 0.02, 0.15)
        cx, cy = pg.display.get_surface().get_size()
        self.muzzle_flash = (cx // 2, cy - 120)
        self.shooting = True
        self.shells.append(ShellEject(cx // 2, cy - 50))
        return True

    def start_reload(self):
        if not self.reloading and self.ammo < self.mag_size and self.reserve > 0:
            self.reloading = True
            self.reload_timer = self.reload_time

    def update(self, dt, moving=False):
        self.fire_cooldown = max(0, self.fire_cooldown - dt)
        self.kickback = max(0, self.kickback - dt * 16)
        self.recoil_angle = max(0, self.recoil_angle - dt * 2)
        if moving:
            self.bob_phase += dt * 10
            self.bob_offset = math.sin(self.bob_phase) * 3
        else:
            self.bob_offset *= 0.9
        if self.shooting and self.muzzle_flash:
            self.muzzle_flash = None
            self.shooting = False
        self.shells = [s for s in self.shells if s.update(dt)]
        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                need = self.mag_size - self.ammo
                give = min(need, self.reserve)
                self.ammo += give
                self.reserve -= give
                self.reloading = False

    def _draw_part(self, screen, vertices, color, border=None):
        if len(vertices) < 2:
            return
        if len(vertices) == 2:
            pg.draw.line(screen, color, vertices[0], vertices[1], max(1, border or 2))
            return
        pg.draw.polygon(screen, color, vertices)
        if border:
            pg.draw.polygon(screen, border, vertices, 1)

    def draw(self, screen, width, height):
        pass

    def draw_muzzle(self, screen):
        if self.muzzle_flash:
            mf_x, mf_y = self.muzzle_flash
            for r in range(16, 0, -2):
                pg.draw.circle(screen, (255, 255 - r * 8, 180 - r * 6), (mf_x, mf_y), r)
        for shell in self.shells:
            shell.draw(screen)

    def draw_reload_bar(self, screen, width, height):
        if self.reloading:
            progress = 1 - (self.reload_timer / self.reload_time)
            bar_w = 200
            bar_x = width // 2 - bar_w // 2
            bar_y = height - 90
            pg.draw.rect(screen, (40, 40, 40), (bar_x - 1, bar_y - 1, bar_w + 2, 12))
            pg.draw.rect(screen, (200, 160, 60), (bar_x, bar_y, int(bar_w * progress), 10))
            pg.draw.rect(screen, (255, 220, 100), (bar_x, bar_y, int(bar_w * progress * 1.2), 5))


class AK47(BaseWeapon):
    def __init__(self):
        super().__init__()
        self.name = "AK47"
        self.damage = 30
        self.fire_rate = 0.1
        self.mag_size = 30
        self.ammo = 30
        self.reserve = 90
        self.reload_time = 2.4

    def apply_upgrades(self, upgrades):
        if "Extended Mag" in upgrades:
            self.mag_size = 45
            self.ammo = min(self.ammo, self.mag_size)
            self.reserve = max(self.reserve, 120)
        if "Damage Boost" in upgrades:
            self.damage = 40
        if "Rapid Fire" in upgrades:
            self.fire_rate = 0.07

    def draw(self, screen, width, height):
        sway_x = math.sin(pg.time.get_ticks() * 0.002) * 1.5 + self.bob_offset
        sway_y = math.sin(pg.time.get_ticks() * 0.003) * 2 + self.kickback * 1.5

        gun_surf = _get_weapon_surface("Gun", int(width * 0.45), int(height * 0.52))
        if gun_surf is not None:
            gx = width // 2 - int(gun_surf.get_width() * 0.35) + int(sway_x)
            gy = height - gun_surf.get_height() + int(sway_y)
            screen.blit(gun_surf, (gx, gy))
        else:
            self._draw_polygon_ak47(screen, width, height, sway_x, sway_y)

        self.draw_muzzle(screen)
        self.draw_reload_bar(screen, width, height)

    def _draw_polygon_ak47(self, screen, width, height, sway_x, sway_y):
        bx = width // 2 + sway_x
        by = height - 140 + sway_y

        stock_pts = [(bx - 28, by - 28), (bx - 70, by - 20), (bx - 74, by - 12), (bx - 28, by - 10)]
        self._draw_part(screen, stock_pts, (100, 72, 40), (60, 40, 20))
        self._draw_part(screen, [(bx - 74, by - 12), (bx - 76, by), (bx - 72, by + 18), (bx - 70, by - 8)], (60, 50, 30), (35, 30, 15))
        self._draw_part(screen, [(bx - 28, by - 28), (bx - 70, by - 20), (bx - 66, by - 26), (bx - 28, by - 34)], (90, 65, 35))

        rec_pts = [(bx - 28, by - 34), (bx + 60, by - 34), (bx + 60, by - 18), (bx - 28, by - 10)]
        self._draw_part(screen, rec_pts, (70, 65, 55), (45, 40, 35))
        self._draw_part(screen, [(bx - 28, by - 34), (bx + 60, by - 34), (bx + 56, by - 40), (bx - 22, by - 40)], (85, 78, 65), (55, 50, 42))
        self._draw_part(screen, [(bx - 24, by - 32), (bx + 56, by - 32), (bx + 56, by - 28), (bx - 24, by - 28)], (100, 92, 78))

        barrel_pts = [(bx + 60, by - 32), (bx + 140, by - 28), (bx + 140, by - 24), (bx + 60, by - 26)]
        self._draw_part(screen, barrel_pts, (55, 50, 45), (35, 30, 28))
        pg.draw.line(screen, (80, 75, 70), (bx + 62, by - 30), (bx + 138, by - 27), 2)

        self._draw_part(screen, [(bx + 20, by - 40), (bx + 55, by - 40), (bx + 55, by - 46), (bx + 20, by - 46)], (65, 58, 48), (40, 35, 28))
        pg.draw.line(screen, (90, 82, 70), (bx + 22, by - 42), (bx + 53, by - 42), 2)

        hg_pts = [(bx + 20, by - 20), (bx + 56, by - 26), (bx + 56, by - 40), (bx + 20, by - 46), (bx - 10, by - 38), (bx - 10, by - 22)]
        self._draw_part(screen, hg_pts, (130, 85, 45), (80, 50, 25))
        for i in range(4):
            gx = bx + 5 + i * 12
            pg.draw.line(screen, (110, 70, 35), (gx, by - 24 + i * 2), (gx + 8, by - 38 + i * 2), 1)

        mag_pts = [(bx + 10, by - 18), (bx + 44, by - 18), (bx + 50, by + 10), (bx + 4, by + 10)]
        self._draw_part(screen, mag_pts, (75, 65, 50), (45, 38, 28))
        for i in range(3):
            rx = bx + 12 + i * 12
            pg.draw.line(screen, (55, 48, 38), (rx, by - 16), (rx + 4, by + 8), 2)

        self._draw_part(screen, [(bx - 10, by - 12), (bx + 8, by - 12), (bx + 2, by + 14), (bx - 14, by + 12)], (100, 72, 40), (60, 40, 20))
        for i in range(3):
            gy = by - 6 + i * 6
            pg.draw.line(screen, (80, 55, 30), (bx - 8, gy), (bx + 6, gy + 2), 1)

        self._draw_part(screen, [(bx + 130, by - 34), (bx + 134, by - 34), (bx + 134, by - 42), (bx + 130, by - 42)], (50, 45, 40), (30, 28, 25))
        self._draw_part(screen, [(bx + 4, by - 40), (bx + 12, by - 40), (bx + 12, by - 46), (bx + 4, by - 46)], (50, 45, 40), (30, 28, 25))

        self._draw_part(screen, [(bx + 140, by - 30), (bx + 148, by - 30), (bx + 148, by - 22), (bx + 140, by - 22)], (60, 55, 48), (38, 35, 30))
        for i in range(3):
            hx = bx + 142 + i * 2
            pg.draw.rect(screen, (30, 28, 25), (hx, by - 28, 1, 4))

        pg.draw.rect(screen, (50, 45, 40), (bx + 40, by - 48, 8, 4))
        pg.draw.rect(screen, (70, 65, 58), (bx + 41, by - 47, 6, 2))


class Glock19(BaseWeapon):
    def __init__(self):
        super().__init__()
        self.name = "Glock19"
        self.damage = 25
        self.fire_rate = 0.18
        self.mag_size = 17
        self.ammo = 17
        self.reserve = 68
        self.reload_time = 1.8

    def apply_upgrades(self, upgrades):
        if "Extended Mag" in upgrades:
            self.mag_size = 25
            self.ammo = min(self.ammo, self.mag_size)
            self.reserve = max(self.reserve, 75)
        if "Damage Boost" in upgrades:
            self.damage = 33
        if "Rapid Fire" in upgrades:
            self.fire_rate = 0.12

    def draw(self, screen, width, height):
        sway_x = math.sin(pg.time.get_ticks() * 0.002) * 1.2 + self.bob_offset * 0.8
        sway_y = math.sin(pg.time.get_ticks() * 0.003) * 1.5 + self.kickback * 1.2

        gun_surf = _get_weapon_surface("Glock19", int(width * 0.4), int(height * 0.48))
        if gun_surf is not None:
            gx = width // 2 + 40 - int(gun_surf.get_width() * 0.4) + int(sway_x)
            gy = height - gun_surf.get_height() + int(sway_y)
            screen.blit(gun_surf, (gx, gy))
        else:
            self._draw_polygon_glock19(screen, width, height, sway_x, sway_y)

        self.draw_muzzle(screen)
        self.draw_reload_bar(screen, width, height)

    def _draw_polygon_glock19(self, screen, width, height, sway_x, sway_y):
        bx = width // 2 + sway_x + 20
        by = height - 100 + sway_y

        slide = [(bx - 20, by - 44), (bx + 48, by - 44), (bx + 48, by - 34), (bx - 20, by - 34)]
        self._draw_part(screen, slide, (55, 55, 58), (35, 35, 38))
        self._draw_part(screen, [(bx - 18, by - 43), (bx + 46, by - 43), (bx + 46, by - 40), (bx - 18, by - 40)], (72, 72, 75))

        barrel_tip = [(bx + 48, by - 44), (bx + 56, by - 42), (bx + 56, by - 36), (bx + 48, by - 34)]
        self._draw_part(screen, barrel_tip, (48, 48, 50), (30, 30, 32))

        self._draw_part(screen, [(bx + 56, by - 40), (bx + 60, by - 39), (bx + 60, by - 37), (bx + 56, by - 38)], (35, 35, 38))

        frame = [(bx - 14, by - 34), (bx + 30, by - 34), (bx + 30, by - 22), (bx - 14, by - 22)]
        self._draw_part(screen, frame, (65, 62, 55), (40, 38, 33))

        grip_pts = [(bx - 8, by - 22), (bx + 14, by - 22), (bx + 8, by + 18), (bx - 14, by + 16)]
        self._draw_part(screen, grip_pts, (50, 48, 42), (30, 28, 24))
        for i in range(4):
            gy = by - 16 + i * 8
            pg.draw.line(screen, (40, 38, 32), (bx - 5, gy), (bx + 10, gy + 1), 1)

        mag_pts = [(bx - 4, by - 20), (bx + 16, by - 20), (bx + 14, by + 12), (bx - 2, by + 12)]
        self._draw_part(screen, mag_pts, (58, 55, 48), (35, 33, 28))

        trigger_guard = [(bx - 10, by - 24), (bx + 6, by - 24), (bx + 4, by - 14), (bx - 6, by - 14)]
        self._draw_part(screen, trigger_guard, (55, 52, 45))

        trigger = [(bx - 2, by - 20), (bx + 1, by - 20), (bx, by - 14)]
        self._draw_part(screen, trigger, (45, 42, 38))

        self._draw_part(screen, [(bx + 4, by - 46), (bx + 8, by - 46), (bx + 8, by - 44), (bx + 4, by - 44)], (42, 42, 45))
        self._draw_part(screen, [(bx + 42, by - 46), (bx + 46, by - 46), (bx + 46, by - 44), (bx + 42, by - 44)], (42, 42, 45))


class Knife(BaseWeapon):
    def __init__(self):
        super().__init__()
        self.name = "Knife"
        self.damage = 60
        self.fire_rate = 0.5
        self.mag_size = 999
        self.ammo = 999
        self.reserve = 999
        self.reload_time = 0
        self.is_melee = True
        self.swing_timer = 0.0
        self.swinging = False
        self.swing_phase = 0

    def apply_upgrades(self, upgrades):
        pass

    def shoot(self):
        if self.fire_cooldown > 0:
            return False
        self.fire_cooldown = self.fire_rate
        self.swinging = True
        self.swing_timer = 0.3
        self.swing_phase = 0
        return True

    def update(self, dt, moving=False):
        super().update(dt, moving)
        if self.swinging:
            self.swing_timer -= dt
            self.swing_phase += dt * 20
            if self.swing_timer <= 0:
                self.swinging = False

    def draw(self, screen, width, height):
        bob = self.bob_offset * 0.5
        sway_x = math.sin(pg.time.get_ticks() * 0.002) * 3 + bob
        sway_y = math.sin(pg.time.get_ticks() * 0.003) * 2

        if self.swinging:
            swing = math.sin(self.swing_phase) * 60
            sway_x += swing * 0.5
            sway_y -= abs(swing) * 0.3

        knife_surf = _get_weapon_surface("Knife", int(width * 0.5), int(height * 0.7))
        if knife_surf is not None:
            gx = width // 2 + 120 - int(knife_surf.get_width() * 0.5) + int(sway_x)
            gy = height // 2 + 40 - int(knife_surf.get_height() * 0.5) + int(sway_y)
            screen.blit(knife_surf, (gx, gy))
        else:
            self._draw_polygon_knife(screen, width, height, sway_x, sway_y)

    def _draw_polygon_knife(self, screen, width, height, sway_x, sway_y):
        bx = width // 2
        by = height // 2

        ox = bx + 120 + sway_x
        oy = by + 120 + sway_y

        blade = [
            (ox - 4, oy - 60), (ox + 4, oy - 60),
            (ox + 3, oy + 10), (ox - 3, oy + 10),
        ]
        self._draw_part(screen, blade, (190, 195, 200), (140, 145, 150))
        self._draw_part(screen, [(ox - 2, oy - 58), (ox + 2, oy - 58), (ox + 1, oy + 8), (ox - 1, oy + 8)], (210, 215, 220))

        edge_pts = [(ox + 4, oy - 60), (ox + 6, oy - 55), (ox + 5, oy + 10), (ox + 3, oy + 10)]
        self._draw_part(screen, edge_pts, (170, 175, 180))

        guard = [(ox - 12, oy + 10), (ox + 12, oy + 10), (ox + 12, oy + 16), (ox - 12, oy + 16)]
        self._draw_part(screen, guard, (80, 75, 65), (55, 50, 42))

        grip = [
            (ox - 6, oy + 16), (ox + 6, oy + 16),
            (ox + 4, oy + 46), (ox - 4, oy + 46),
        ]
        self._draw_part(screen, grip, (100, 72, 40), (60, 40, 20))
        for i in range(5):
            gy = oy + 20 + i * 5
            pg.draw.line(screen, (80, 55, 30), (ox - 4, gy), (ox + 4, gy), 1)

        pommel = [(ox - 5, oy + 46), (ox + 5, oy + 46), (ox + 4, oy + 52), (ox - 4, oy + 52)]
        self._draw_part(screen, pommel, (65, 60, 50), (40, 35, 30))


class Grenade(BaseWeapon):
    def __init__(self):
        super().__init__()
        self.name = "Grenade"
        self.damage = 50
        self.fire_rate = 0.8
        self.mag_size = 1
        self.ammo = 1
        self.reserve = 0
        self.reload_time = 0
        self.is_throwable = True
        self.throw_cooldown = 0.0

    def apply_upgrades(self, upgrades):
        if "More Damage" in upgrades:
            self.damage = 75
        if "Blast Radius" in upgrades:
            self.damage = 50

    def shoot(self):
        if self.fire_cooldown > 0:
            return False
        self.fire_cooldown = self.fire_rate
        return True

    def update(self, dt, moving=False):
        super().update(dt, moving)
        self.throw_cooldown = max(0, self.throw_cooldown - dt)

    def draw(self, screen, width, height):
        sway_x = math.sin(pg.time.get_ticks() * 0.002) * 2 + self.bob_offset * 0.6
        sway_y = math.sin(pg.time.get_ticks() * 0.003) * 1.5

        grenade_surf = _get_weapon_surface("grenade", int(width * 0.28), int(height * 0.34))
        if grenade_surf is not None:
            gx = width // 2 + 40 - int(grenade_surf.get_width() * 0.5) + int(sway_x)
            gy = height - grenade_surf.get_height() + int(sway_y)
            screen.blit(grenade_surf, (gx, gy))
        else:
            self._draw_polygon_grenade(screen, width, height, sway_x, sway_y)

        self.draw_reload_bar(screen, width, height)

    def _draw_polygon_grenade(self, screen, width, height, sway_x, sway_y):
        bx = width // 2 + 80 + int(sway_x)
        by = height - 100 + int(sway_y)

        body = [
            (bx - 16, by - 20), (bx + 16, by - 20),
            (bx + 18, by + 16), (bx - 18, by + 16),
        ]
        self._draw_part(screen, body, (70, 85, 55), (45, 55, 35))

        for i in range(4):
            rx = bx - 12 + i * 8
            pg.draw.line(screen, (55, 70, 42), (rx, by - 18), (rx + 2, by + 14), 1)
        for i in range(5):
            ry = by - 16 + i * 8
            pg.draw.line(screen, (55, 70, 42), (bx - 15, ry), (bx + 15, ry), 1)

        top = [(bx - 10, by - 24), (bx + 10, by - 24), (bx + 8, by - 20), (bx - 8, by - 20)]
        self._draw_part(screen, top, (90, 85, 70), (60, 55, 45))

        pin = [(bx + 6, by - 30), (bx + 10, by - 30), (bx + 10, by - 24), (bx + 6, by - 24)]
        self._draw_part(screen, pin, (160, 155, 140), (110, 105, 95))

        lever = [(bx - 2, by - 32), (bx + 4, by - 32), (bx + 2, by - 24), (bx - 4, by - 24)]
        self._draw_part(screen, lever, (130, 125, 110), (90, 85, 75))


class ShellEject:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-60, -20)
        self.vy = random.uniform(-100, -50)
        self.life = 1.0
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-600, 600)

    def update(self, dt):
        self.life -= dt
        self.vy += 600 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rot_speed * dt
        return self.life > 0

    def draw(self, screen):
        cx, cy = int(self.x), int(self.y)
        w, h = 6, 4
        cos_a = math.cos(math.radians(self.rotation))
        sin_a = math.sin(math.radians(self.rotation))
        pts = [
            (cx + (-w // 2) * cos_a - (-h // 2) * sin_a, cy + (-w // 2) * sin_a + (-h // 2) * cos_a),
            (cx + (w // 2) * cos_a - (-h // 2) * sin_a, cy + (w // 2) * sin_a + (-h // 2) * cos_a),
            (cx + (w // 2) * cos_a - (h // 2) * sin_a, cy + (w // 2) * sin_a + (h // 2) * cos_a),
            (cx + (-w // 2) * cos_a - (h // 2) * sin_a, cy + (-w // 2) * sin_a + (h // 2) * cos_a),
        ]
        base_color = (180, 150, 80)
        pg.draw.polygon(screen, base_color, pts)
        pg.draw.polygon(screen, (120, 90, 50), pts, 1)


WEAPON_CLASSES = {
    "AK47": AK47,
    "Glock19": Glock19,
    "Knife": Knife,
    "Grenade": Grenade,
}
