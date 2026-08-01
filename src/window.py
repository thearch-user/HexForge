import math
import random
import numpy as np
import pygame as pg
from config import *
from map import Map, TILE_FLOOR, TILE_WATER, TILE_GRASS, TILE_DOOR
from loadout import AK47, Glock19, Knife, Grenade, M16AI, DesertEagle, Katana, Molotov
from textures import TEXTURES, TEXTURE_NAMES, TEX_SIZE, get_texture
from bullet import Bullet
from target import Target
from opengl_renderer import OpenGLRenderer, scancode_to_pygame, SDL_KEYDOWN, SDL_KEYUP, SDL_QUIT, SDL_MOUSEMOTION, SDL_MOUSEBUTTONDOWN, SDL_MOUSEBUTTONUP, SDL_WINDOWEVENT
import sound
import game_state
import ctypes

pg.init()
pg.mixer.init()
sound.init()

RENDER_W = SCREEN_WIDTH // RENDER_SCALE
RENDER_H = SCREEN_HEIGHT // RENDER_SCALE

renderer = OpenGLRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
clock = pg.time.Clock()

game_map = Map()
spawn = game_map.get_spawn()

px, py = spawn
pdx, pdy = 1.0, 0.0
pitch = 0.0
angle = 0.0
player_z = 0.0
player_vz = 0.0
on_ground = True
aiming = False
display_fov = FOV
player_hp = PLAYER_MAX_HP
wave = 0
damage_flash = 0.0
death_timer = 0.0

weapons = {"AK47": AK47(), "Glock19": Glock19(), "Knife": Knife(), "Grenade": Grenade(),
           "M16AI": M16AI(), "DesertEagle": DesertEagle(), "Katana": Katana(), "Molotov": Molotov()}
for name, w in weapons.items():
    if hasattr(w, 'apply_upgrades'):
        ups = game_state.get_upgrades(name) + game_state.get_upgrades("AK47")
        w.apply_upgrades(ups)
grenade_count = game_state.get_grenades()
weapons["Grenade"].ammo = grenade_count
weapons["Grenade"].reserve = grenade_count
molotov_count = game_state.get_molotovs()
weapons["Molotov"].ammo = molotov_count
weapons["Molotov"].reserve = molotov_count

current_weapon = "AK47"
bullets = []
thrown_grenades = []
thrown_molotovs = []
fire_pools = []
impact_particles = []

floor_tiles = game_map.get_floor_tiles()
random.shuffle(floor_tiles)
targets = []
placed = 0
for tx, ty in floor_tiles:
    if placed >= 8:
        break
    if abs(tx - int(spawn[0])) < 5 and abs(ty - int(spawn[1])) < 5:
        continue
    targets.append(Target(tx + 0.5, ty + 0.5, placed, wave=wave))
    placed += 1

tex_cols_np = np.array([
    pg.surfarray.array3d(get_texture(name))
    for name in TEXTURE_NAMES
], dtype=np.uint8)

floor_cols_np = pg.surfarray.array3d(get_texture("cobblestone")).astype(np.uint8)
ceil_cols_np = pg.surfarray.array3d(get_texture("concrete")).astype(np.uint8)
grass_cols_np = pg.surfarray.array3d(get_texture("grass")).astype(np.uint8)
water_cols_np = pg.surfarray.array3d(get_texture("water")).astype(np.uint8)

map_grid = np.zeros((game_map.height, game_map.width), dtype=np.uint8)
map_tex_ids = np.zeros((game_map.height, game_map.width), dtype=np.uint8)
map_floor = np.zeros((game_map.height, game_map.width), dtype=np.uint8)
for y in range(game_map.height):
    for x in range(game_map.width):
        map_grid[y, x] = game_map.grid[y][x]
        map_tex_ids[y, x] = game_map.tex_map[y][x]
        map_floor[y, x] = game_map.floor_type[y][x]

map_tex = renderer.create_map_texture(game_map.grid, game_map.tex_map, game_map.floor_type, game_map.width, game_map.height)
wall_tex = renderer.create_wall_texture_array(list(tex_cols_np))
floor_tex = renderer.create_texture_2d(floor_cols_np)
ceil_tex = renderer.create_texture_2d(ceil_cols_np)
grass_tex = renderer.create_texture_2d(grass_cols_np)
water_tex = renderer.create_texture_2d(water_cols_np)

try:
    font = pg.font.SysFont("segoeui", 22)
    font_small = pg.font.SysFont("segoeui", 16)
    font_big = pg.font.SysFont("segoeui", 28, bold=True)
    font_tiny = pg.font.SysFont("segoeui", 13)
except Exception:
    font = pg.font.SysFont("arial", 22)
    font_small = pg.font.SysFont("arial", 16)
    font_big = pg.font.SysFont("arial", 28, bold=True)
    font_tiny = pg.font.SysFont("arial", 13)

hud_tex_id = None
hud_w, hud_h = 0, 0


def spawn_targets():
    global targets
    floor_tiles = game_map.get_floor_tiles()
    random.shuffle(floor_tiles)
    targets = []
    placed = 0
    for tx, ty in floor_tiles:
        if placed >= 8:
            break
        if abs(tx - int(spawn[0])) < 5 and abs(ty - int(spawn[1])) < 5:
            continue
        targets.append(Target(tx + 0.5, ty + 0.5, placed, wave=wave))
        placed += 1


def emit_impact(x, y, count=12):
    for _ in range(count):
        ap = random.uniform(0, math.pi * 2)
        speed = random.uniform(20, 80)
        vz = random.uniform(30, 120)
        color = random.choice([(180, 160, 140), (160, 140, 120), (200, 180, 160)])
        impact_particles.append({
            'x': x, 'y': y, 'z': 0,
            'vx': math.cos(ap) * speed, 'vy': math.sin(ap) * speed, 'vz': vz,
            'color': color, 'life': random.uniform(0.2, 0.6),
        })


def project_point(wx, wy, ppx, ppy, pangle, fov, w, h):
    dx = wx - ppx
    dy = wy - ppy
    dist = math.hypot(dx, dy)
    if dist < 0.3 or dist > 18.0:
        return None
    angle_to = math.atan2(dy, dx)
    diff = angle_to - pangle
    while diff > math.pi:
        diff -= 2 * math.pi
    while diff < -math.pi:
        diff += 2 * math.pi
    half_fov = math.radians(fov / 2)
    if abs(diff) > half_fov:
        return None
    sx = int((diff / half_fov) * (w // 2) + w // 2)
    height = int(h / (dist * 1.4))
    sy = h // 2 + int(height * 0.35)
    return sx, sy, dist


def draw_hud(surf, w, h):
    cx, cy = w // 2, h // 2
    gun = weapons[current_weapon]

    if current_weapon not in ("Knife", "Katana"):
        if not gun.reloading:
            pg.draw.line(surf, COLORS["CROSSHAIR"], (cx - 10, cy), (cx + 10, cy), 2)
            pg.draw.line(surf, COLORS["CROSSHAIR"], (cx, cy - 10), (cx, cy + 10), 2)
            pg.draw.circle(surf, COLORS["CROSSHAIR"], (cx, cy), 2, 1)
    else:
        pg.draw.circle(surf, COLORS["CROSSHAIR"], (cx, cy), 8, 1)

    gun.draw(surf, w, h)

    if current_weapon not in ("Knife", "Katana"):
        if current_weapon == "Grenade":
            ammo_str = f"x{game_state.get_grenades()}"
        elif current_weapon == "Molotov":
            ammo_str = f"x{game_state.get_molotovs()}"
        else:
            ammo_str = f"{gun.ammo}/{gun.mag_size}"
        ammo_surf = font.render(ammo_str, True, COLORS["HUD_TEXT"])
        surf.blit(ammo_surf, (w - 150, h - 65))

        if current_weapon not in ("Grenade", "Molotov"):
            reserve_str = str(gun.reserve)
            reserve_s = font_small.render(reserve_str, True, (180, 180, 180))
            surf.blit(reserve_s, (w - 150, h - 42))
            res_lbl = font_small.render("reserve", True, (140, 140, 140))
            surf.blit(res_lbl, (w - 150, h - 28))

    fps_str = f"{int(clock.get_fps())} FPS"
    fps_surf = font_small.render(fps_str, True, (0, 255, 0))
    surf.blit(fps_surf, (12, 12))

    wn_surf = font_big.render(current_weapon, True, (230, 150, 40))
    surf.blit(wn_surf, (w // 2 - wn_surf.get_width() // 2, 16))

    mm_base = game_map.minimap(1)
    overlay = mm_base.copy()
    mm_px = int(px)
    mm_py = int(py)
    pg.draw.circle(overlay, (255, 60, 60), (mm_px, mm_py), 2)
    pg.draw.line(overlay, (255, 255, 100), (mm_px, mm_py),
                 (mm_px + int(pdx * 3), mm_py + int(pdy * 3)), 2)
    for t in targets:
        tx = int(t.x)
        ty = int(t.y)
        if t.alive:
            hp_pct = t.hp / t.max_hp
            if hp_pct > 0.5:
                mc = (0, 255, 80)
            elif hp_pct > 0.25:
                mc = (255, 200, 50)
            else:
                mc = (255, 40, 40)
            pg.draw.circle(overlay, mc, (tx, ty), 2)
        else:
            pg.draw.circle(overlay, (100, 100, 100), (tx, ty), 2)
    overlay.set_alpha(160)
    surf.blit(overlay, (12, 38))

    for fp in fire_pools:
        info = project_point(fp.x, fp.y, px, py, angle, display_fov, w, h)
        if info:
            sx, sy, dist = info
            flicker = math.sin(pg.time.get_ticks() * 0.03 + fp.x * 3) * 0.5 + 0.5
            radius = max(4, int((40 - dist * 1.5) * (0.7 + flicker * 0.4)))
            for r in range(radius, 0, -2):
                glow = (255, int(120 + r * 6), int(40 + r * 4))
                pg.draw.circle(surf, glow, (sx, sy), r)

    weapon_slots = [
        ("1", "AK47", game_state.has_weapon("AK47")),
        ("2", "Glock19", game_state.has_weapon("Glock19")),
        ("3", "Knife", game_state.has_weapon("Knife")),
        ("4", "Grenade", game_state.has_weapon("Grenade")),
        ("5", "M16AI", game_state.has_weapon("M16AI")),
        ("6", "DesertEagle", game_state.has_weapon("DesertEagle")),
        ("7", "Katana", game_state.has_weapon("Katana")),
        ("8", "Molotov", game_state.has_weapon("Molotov")),
    ]
    slot_x = w - 200
    slot_y = 16
    slot_step = 44
    for key, wname, owned in weapon_slots:
        if not owned:
            slot_x += slot_step
            continue
        active = current_weapon == wname
        slot_bg = (50, 50, 60) if active else (30, 30, 38)
        slot_border = (230, 150, 40) if active else (60, 60, 70)
        slot_rect = pg.Rect(slot_x, slot_y, 42, 42)
        pg.draw.rect(surf, slot_bg, slot_rect, border_radius=6)
        pg.draw.rect(surf, slot_border, slot_rect, 2, border_radius=6)
        kn = font_tiny.render(key, True, (230, 150, 40) if active else (140, 140, 150))
        surf.blit(kn, (slot_x + 3, slot_y + 3))
        nn = font_tiny.render(wname[:4], True, (255, 255, 255) if active else (100, 100, 110))
        surf.blit(nn, (slot_x + 3, slot_y + 22))
        slot_x += slot_step

    health_bar_y = h - 50
    heart_size = 16
    heart_spacing = 20
    hearts_start_x = w // 2 - (PLAYER_MAX_HP * heart_spacing) // 2
    for i in range(PLAYER_MAX_HP):
        hx = hearts_start_x + i * heart_spacing
        hy = health_bar_y
        if i < int(player_hp):
            draw_heart(surf, hx, hy, heart_size, (220, 40, 40), (180, 20, 20))
        elif i < player_hp:
            draw_heart(surf, hx, hy, heart_size, (150, 40, 40), (120, 20, 20))
        else:
            draw_heart(surf, hx, hy, heart_size, (60, 30, 30), (40, 20, 20))

    wave_txt = font_tiny.render(f"Wave {wave + 1}", True, (230, 150, 40))
    surf.blit(wave_txt, (12, h - 25))

    alive_count = sum(1 for t in targets if t.alive)
    alive_txt = font_tiny.render(f"Enemies: {alive_count}", True, (180, 180, 180))
    surf.blit(alive_txt, (w - 120, h - 25))

    money = game_state.get_money()
    money_txt = font.render(f"${money}", True, (230, 200, 50))
    surf.blit(money_txt, (w - 150, h - 85))


def draw_heart(surf, x, y, size, fill_color, outline_color):
    pts = []
    for i in range(360):
        rad = math.radians(i)
        s = size / 32.0
        hx = s * 16 * math.sin(rad) ** 3
        hy = -s * (13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad))
        pts.append((int(x + hx), int(y + hy)))
    pg.draw.polygon(surf, fill_color, pts)
    pg.draw.polygon(surf, outline_color, pts, 1)


def draw_scope(surf, w, h):
    cx, cy = w // 2, h // 2
    overlay = pg.Surface((w, h), pg.SRCALPHA)
    pg.draw.circle(overlay, (0, 0, 0, 120), (cx, cy), min(w, h) // 2)
    pg.draw.circle(overlay, (0, 0, 0, 0), (cx, cy), min(w, h) // 3)
    scope_r = min(w, h) // 3
    pg.draw.circle(overlay, (200, 200, 200, 180), (cx, cy), scope_r, 2)
    pg.draw.line(overlay, (200, 200, 200, 140), (cx - scope_r, cy), (cx + scope_r, cy), 1)
    pg.draw.line(overlay, (200, 200, 200, 140), (cx, cy - scope_r), (cx, cy + scope_r), 1)
    pg.draw.line(overlay, (255, 60, 60, 100), (cx - 6, cy), (cx + 6, cy), 1)
    pg.draw.line(overlay, (255, 60, 60, 100), (cx, cy - 6), (cx, cy + 6), 1)
    surf.blit(overlay, (0, 0))


running = True


def run():
    global running, bullets, impact_particles, thrown_grenades, current_weapon
    global player_hp, wave, damage_flash, death_timer, angle, pitch, px, py
    global player_z, player_vz, on_ground, aiming, display_fov, pdx, pdy
running = True


class GrenadeProjectile:
    def __init__(self, x, y, angle, damage=50, blast_radius=GRENADE_RADIUS):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * GRENADE_SPEED
        self.vy = math.sin(angle) * GRENADE_SPEED
        self.z = 1.0
        self.vz = GRENADE_ARC
        self.fuse = GRENADE_FUSE
        self.damage = damage
        self.blast_radius = blast_radius
        self.alive = True
        self.exploded = False
        self.explosion_timer = 0.0

    def update(self, dt, game_map, targets):
        if self.exploded:
            self.explosion_timer -= dt
            return self.explosion_timer > 0
        self.fuse -= dt
        if self.fuse <= 0:
            self._explode(targets)
            return True
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.vz -= 15.0 * dt
        self.vx *= 0.99
        self.vy *= 0.99
        if self.z < 0:
            self.z = 0
            self.vz *= -0.2
            self.vx *= 0.5
            self.vy *= 0.5
        if game_map.is_wall(self.x + self.vx * dt * 0.1, self.y):
            self.vx *= -0.3
        if game_map.is_wall(self.x, self.y + self.vy * dt * 0.1):
            self.vy *= -0.3
        return True

    def _explode(self, targets):
        self.exploded = True
        self.explosion_timer = 0.4
        sound.play_explosion()
        for t in targets:
            if not t.alive:
                continue
            dist = math.hypot(t.x - self.x, t.y - self.y)
            if dist < self.blast_radius:
                falloff = 1 - (dist / self.blast_radius)
                dmg = int(self.damage * falloff)
                if dmg > 0:
                    t.hit(dmg)
        emit_impact(self.x, self.y, 30)


class MolotovProjectile:
    def __init__(self, x, y, angle, damage=8):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * GRENADE_SPEED
        self.vy = math.sin(angle) * GRENADE_SPEED
        self.z = 1.0
        self.vz = GRENADE_ARC
        self.damage = damage
        self.alive = True
        self.exploded = False

    def update(self, dt, game_map, targets, fire_pools):
        if self.exploded:
            return False
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.vz -= 15.0 * dt
        if self.z <= 0 or game_map.is_wall(self.x, self.y):
            self.exploded = True
            self._ignite(fire_pools)
            return False
        return True

    def _ignite(self, fire_pools):
        sound.play_explosion()
        fire_pools.append(FirePool(self.x, self.y, self.damage))
        emit_impact(self.x, self.y, 20)


class FirePool:
    def __init__(self, x, y, damage=8, radius=2.5, duration=4.0):
        self.x = x
        self.y = y
        self.damage = damage
        self.radius = radius
        self.duration = duration
        self.timer = duration
        self.tick = 0.0

    def update(self, dt, targets):
        self.timer -= dt
        if self.timer <= 0:
            return False
        self.tick -= dt
        if self.tick <= 0:
            self.tick = 0.25
            for t in targets:
                if not t.alive:
                    continue
                if math.hypot(t.x - self.x, t.y - self.y) < self.radius:
                    t.hit(self.damage)
            emit_impact(self.x, self.y, 8)
        return True


def run():
    global running, bullets, impact_particles, thrown_grenades, thrown_molotovs, fire_pools, current_weapon
    global player_hp, wave, damage_flash, death_timer, angle, pitch, px, py
    global player_z, player_vz, on_ground, aiming, display_fov, pdx, pdy
    running = True
    current_weapon = "AK47"
    start_ticks = SDL_GetTicks()

    while running:
        now_ticks = SDL_GetTicks()
        dt = (now_ticks - start_ticks) / 1000.0
        start_ticks = now_ticks
        if dt > 0.05:
            dt = 0.05
        if dt <= 0:
            dt = 0.001

        event = renderer.poll_event()
        while event is not None:
            etype = event.type
            if etype == SDL_QUIT:
                running = False
                break
            if etype == SDL_KEYDOWN:
                sc = event.key.keysym.scancode
                if sc == 41:
                    running = False
                if sc == 30 and game_state.has_weapon("AK47"):
                    current_weapon = "AK47"
                if sc == 31 and game_state.has_weapon("Glock19"):
                    current_weapon = "Glock19"
                if sc == 32 and game_state.has_weapon("Knife"):
                    current_weapon = "Knife"
                if sc == 33 and game_state.has_weapon("Grenade"):
                    current_weapon = "Grenade"
                if sc == 34 and game_state.has_weapon("M16AI"):
                    current_weapon = "M16AI"
                if sc == 35 and game_state.has_weapon("DesertEagle"):
                    current_weapon = "DesertEagle"
                if sc == 36 and game_state.has_weapon("Katana"):
                    current_weapon = "Katana"
                if sc == 37 and game_state.has_weapon("Molotov"):
                    current_weapon = "Molotov"
            if etype == SDL_WINDOWEVENT:
                renderer.handle_event(event)
            event = renderer.poll_event()

        keys = renderer.get_keys()
        mx, my, m_left, m_right = renderer.get_mouse_rel()

        speed = PLAYER_SPEED * dt
        if game_map.is_water(px, py):
            speed *= 0.5

        dx, dy = 0.0, 0.0
        if 26 in keys:
            dx += pdx * speed
            dy += pdy * speed
        if 22 in keys:
            dx -= pdx * speed
            dy -= pdy * speed
        if 4 in keys:
            dx -= pdy * speed
            dy += pdx * speed
        if 7 in keys:
            dx += pdy * speed
            dy -= pdx * speed

        nx, ny = px + dx, py + dy
        if not game_map.is_wall(nx, ny):
            px, py = nx, ny
        elif not game_map.is_wall(nx, py):
            px = nx
        elif not game_map.is_wall(px, ny):
            py = ny

        if 44 in keys and on_ground:
            player_vz = JUMP_FORCE
            on_ground = False

        player_vz -= GRAVITY * dt
        player_z += player_vz * dt
        if player_z <= 0:
            player_z = 0
            player_vz = 0
            on_ground = True

        aiming = m_right

        angle -= mx * MOUSE_SENSITIVITY
        pitch += my * MOUSE_SENSITIVITY * 8
        pitch = max(-200, min(200, pitch))

        pdx = math.cos(angle)
        pdy = math.sin(angle)

        if 8 in keys:
            look_x = px + pdx * 1.5
            look_y = py + pdy * 1.5
            game_map.try_open_door(look_x, look_y)

        gun = weapons[current_weapon]

        if m_left:
            if current_weapon == "Grenade":
                if gun.shoot():
                    if game_state.use_grenade():
                        throw = GrenadeProjectile(px, py, angle, gun.damage)
                        thrown_grenades.append(throw)
                        gun.ammo = game_state.get_grenades()
                        sound.play_grenade_throw()
            elif current_weapon == "Molotov":
                if gun.shoot():
                    if game_state.use_molotov():
                        mol = MolotovProjectile(px, py, angle, gun.damage)
                        thrown_molotovs.append(mol)
                        gun.ammo = game_state.get_molotovs()
                        sound.play_grenade_throw()
            elif current_weapon in ("Knife", "Katana"):
                if gun.shoot():
                    sound.play_knife()
                    for t in targets:
                        if not t.alive:
                            continue
                        dist = math.hypot(t.x - px, t.y - py)
                        if dist < MELEE_RANGE:
                            dx_a = t.x - px
                            dy_a = t.y - py
                            angle_to = math.atan2(dy_a, dx_a)
                            diff = angle_to - angle
                            while diff > math.pi:
                                diff -= 2 * math.pi
                            while diff < -math.pi:
                                diff += 2 * math.pi
                            if abs(diff) < math.radians(FOV / 2 * 1.5):
                                t.hit(gun.damage)
                                emit_impact(t.x, t.y, 5)
            elif current_weapon in ("Glock19", "DesertEagle"):
                if gun.shoot():
                    bullets.append(Bullet(px, py, angle, damage=gun.damage))
                    sound.play_pistol()
            else:
                if gun.shoot():
                    for _ in range(gun.pellets):
                        spread = random.uniform(-gun.spread, gun.spread) if gun.spread else 0.0
                        bullets.append(Bullet(px, py, angle + spread, damage=gun.damage))
                    sound.play_gunshot()

        if 21 in keys:
            gun.start_reload()

        gun.update(dt, False)

        game_map.update_doors(dt)

        still_alive = []
        for b in bullets:
            alive = b.update(dt, game_map, targets)
            if b.hit_target:
                sound.play_hit()
                emit_impact(b.x, b.y)
            if not alive and b.hit_pos and not b.hit_target:
                emit_impact(b.hit_pos[0], b.hit_pos[1])
            if alive:
                still_alive.append(b)
        bullets = still_alive

        still_grenades = []
        for g in thrown_grenades:
            alive = g.update(dt, game_map, targets)
            if g.exploded and g.explosion_timer > 0:
                still_grenades.append(g)
            elif alive:
                still_grenades.append(g)
        thrown_grenades = still_grenades

        still_molotovs = []
        for m in thrown_molotovs:
            alive = m.update(dt, game_map, targets, fire_pools)
            if alive:
                still_molotovs.append(m)
        thrown_molotovs = still_molotovs

        fire_pools = [f for f in fire_pools if f.update(dt, targets)]

        for t in targets:
            was_alive = t.alive
            t.update(dt, px, py, game_map)
            if was_alive and not t.alive:
                game_state.earn(KILL_REWARD)

        all_enemy_bullets = []
        for t in targets:
            for eb in t.enemy_bullets:
                if eb.alive:
                    eb_dist = math.hypot(eb.x - px, eb.y - py)
                    if eb_dist < 0.5:
                        eb.alive = False
                        player_hp -= ENEMY_BULLET_DAMAGE
                        damage_flash = 0.3
                        sound.play_hit()
                    else:
                        all_enemy_bullets.append(eb)

        if player_hp <= 0:
            player_hp = 0
            death_timer += dt
            if death_timer > 2.0:
                player_hp = PLAYER_MAX_HP
                death_timer = 0
                wave = 0
                spawn_targets()

        damage_flash = max(0, damage_flash - dt)

        alive_enemies = [t for t in targets if t.alive]
        if len(alive_enemies) == 0:
            wave += 1
            spawn_targets()

        display_fov = AIM_FOV if aiming else FOV
        time_val = (now_ticks) / 1000.0

        renderer.begin_frame()
        renderer.render_scene(
            px, py, angle, pitch, display_fov, player_z,
            map_tex, wall_tex, floor_tex, ceil_tex, grass_tex, water_tex,
            game_map.width, game_map.height, len(TEXTURE_NAMES),
            time_val, damage_flash,
        )

        hud_surf = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        hud_surf.fill((0, 0, 0, 0))
        draw_hud(hud_surf, SCREEN_WIDTH, SCREEN_HEIGHT)

        if damage_flash > 0:
            flash_alpha = int(180 * (damage_flash / 0.3))
            flash_s = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
            flash_s.fill((255, 0, 0, flash_alpha))
            hud_surf.blit(flash_s, (0, 0))

        if player_hp <= 0:
            death_s = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
            death_s.fill((0, 0, 0, 160))
            hud_surf.blit(death_s, (0, 0))
            death_txt = font_big.render("YOU DIED", True, (220, 40, 40))
            hud_surf.blit(death_txt, (SCREEN_WIDTH // 2 - death_txt.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        if aiming:
            draw_scope(hud_surf, SCREEN_WIDTH, SCREEN_HEIGHT)

        hud_data = pg.image.tostring(hud_surf, "RGBA", True)
        hud_w = SCREEN_WIDTH
        hud_h = SCREEN_HEIGHT
        renderer.end_frame_with_hud(hud_data, hud_w, hud_h)

    renderer.quit()
    pg.quit()


if __name__ == "__main__":
    run()
