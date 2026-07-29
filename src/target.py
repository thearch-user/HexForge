import math
import random
import pygame as pg
from config import ENEMY_SHOOT_RANGE, ENEMY_SHOOT_COOLDOWN, ENEMY_BULLET_DAMAGE, ENEMY_SPEED_BASE, ENEMY_SPEED_WAVE_BONUS, ENEMY_HP_BASE, ENEMY_HP_WAVE_BONUS


class Target:
    def __init__(self, x, y, id_num=0, wave=0):
        self.x = x
        self.y = y
        self.id = id_num
        self.wave = wave
        hp_bonus = ENEMY_HP_WAVE_BONUS * wave
        self.max_hp = ENEMY_HP_BASE + hp_bonus
        self.hp = self.max_hp
        self.alive = True
        self.hit_flash = 0.0
        self.fallen_timer = 0.0
        self.shoot_cooldown = random.uniform(0.5, ENEMY_SHOOT_COOLDOWN)
        self.speed = ENEMY_SPEED_BASE + ENEMY_SPEED_WAVE_BONUS * wave
        self.enemy_bullets = []
        self.arm_phase = 0.0

    def hit(self, damage):
        if not self.alive:
            return False
        self.hp -= damage
        self.hit_flash = 0.15
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.fallen_timer = 0.5
        return True

    def update(self, dt, player_x=None, player_y=None, game_map=None):
        self.hit_flash = max(0, self.hit_flash - dt)
        if not self.alive:
            self.fallen_timer = max(0, self.fallen_timer - dt)
            self.enemy_bullets = [b for b in self.enemy_bullets if b.update(dt)]
            return

        self.enemy_bullets = [b for b in self.enemy_bullets if b.update(dt)]

        if player_x is None or player_y is None:
            return

        dx = player_x - self.x
        dy = player_y - self.y
        dist = math.hypot(dx, dy)

        if dist > 0.1:
            move_x = (dx / dist) * self.speed * dt
            move_y = (dy / dist) * self.speed * dt
            new_x = self.x + move_x
            new_y = self.y + move_y
            if game_map and not game_map.is_wall(new_x, new_y):
                if dist > 2.5:
                    self.x = new_x
                    self.y = new_y

        self.shoot_cooldown -= dt
        if self.shoot_cooldown <= 0 and dist < ENEMY_SHOOT_RANGE and dist > 1.5:
            self.shoot_cooldown = ENEMY_SHOOT_COOLDOWN + random.uniform(-0.3, 0.3)
            angle_to_player = math.atan2(dy, dx)
            spread = random.uniform(-0.15, 0.15)
            self.enemy_bullets.append(EnemyBullet(
                self.x, self.y, angle_to_player + spread
            ))
            self.arm_phase = 0.0

        self.arm_phase += dt * 8

    def get_screen_info(self, px, py, pangle, fov, w, h):
        dx = self.x - px
        dy = self.y - py
        dist = math.hypot(dx, dy)
        if dist < 0.3:
            return None

        angle_to = math.atan2(dy, dx)
        diff = angle_to - pangle
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi

        half_fov = math.radians(fov / 2)
        if abs(diff) > half_fov + 0.1:
            return None

        screen_x = int((diff / half_fov) * (w // 2) + w // 2)
        if screen_x < -200 or screen_x >= w + 200:
            return None

        height = int(h / (dist * 1.4))
        width = int(height * 0.45)
        if width < 2:
            return None
        screen_y = h // 2 - height // 2

        return screen_x, screen_y, width, height, dist

    def draw_flat(self, screen, sx, sy, sw, sh):
        if not self.alive:
            fall_progress = 1 - (self.fallen_timer / 0.5) if self.fallen_timer > 0 else 1
            sh = int(sh * (1 - fall_progress * 0.7))
            sy = sy + (sh if fall_progress > 0 else 0)

        if self.wave > 0:
            wave_tint = min(1.0, self.wave * 0.15)
            base_r = int(100 + 120 * wave_tint)
            base_g = int(140 - 60 * wave_tint)
            base_b = int(200 - 80 * wave_tint)
        else:
            base_r, base_g, base_b = 100, 140, 200

        if self.hit_flash > 0:
            base_color = (220, 50, 50)
        elif not self.alive:
            base_color = (70, 70, 70)
        else:
            base_color = (base_r, base_g, base_b)

        body_h = int(sh * 0.65)
        head_r = int(sw * 0.3)

        pg.draw.rect(screen, base_color, (sx - sw // 2, sy + int(sh * 0.35), sw, int(sh * 0.65)))
        pg.draw.circle(screen, base_color, (sx, sy + int(sh * 0.25)), head_r)

        if self.alive and self.wave > 0:
            crown_y = sy + int(sh * 0.12)
            crown_color = (255, 200 + min(55, self.wave * 20), 50)
            pg.draw.polygon(screen, crown_color, [
                (sx - head_r, crown_y + head_r),
                (sx - head_r + 3, crown_y),
                (sx, crown_y + head_r - 3),
                (sx + head_r - 3, crown_y),
                (sx + head_r, crown_y + head_r),
            ])

        if self.alive:
            cx, cy = sx, sy + int(sh * 0.5)
            r_inner = max(1, int(sw * 0.12))
            pg.draw.circle(screen, (255, 60, 60), (cx, cy), max(1, int(sw * 0.2)), 2)
            pg.draw.circle(screen, (255, 60, 60), (cx, cy), r_inner, 1)


class EnemyBullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 10.0
        self.life = 1.0
        self.alive = True
        self.hit_player = False

    def update(self, dt):
        if not self.alive:
            return False
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return False
        dx = math.cos(self.angle) * self.speed * dt
        dy = math.sin(self.angle) * self.speed * dt
        self.x += dx
        self.y += dy
        return True

    def draw(self, screen, px, py, pdx, pdy, fov):
        if not self.alive:
            return
        dx = self.x - px
        dy = self.y - py
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
        half_fov = math.radians(fov / 2)
        if abs(diff) > half_fov:
            return
        from config import SCREEN_WIDTH, SCREEN_HEIGHT
        screen_x = int((diff / half_fov) * (SCREEN_WIDTH // 2) + SCREEN_WIDTH // 2)
        screen_h = int(SCREEN_HEIGHT / dist * 0.12)
        screen_y = SCREEN_HEIGHT // 2 - screen_h // 2
        if 0 <= screen_x < SCREEN_WIDTH:
            pg.draw.rect(screen, (255, 80, 40), (screen_x - 1, screen_y + screen_h // 2, 3, max(1, screen_h // 2)))
