import math
import random
import numpy as np
import pygame as pg
from config import *
from map import Map, TILE_FLOOR, TILE_WATER, TILE_GRASS, TILE_DOOR
from loadout import AK47, Glock19, Knife, Grenade, WEAPON_CLASSES
from textures import TEXTURES, TEXTURE_NAMES, TEX_SIZE, get_texture
from bullet import Bullet
from target import Target
import sound
import game_state

pg.init()
sound.init()

RENDER_W = SCREEN_WIDTH // RENDER_SCALE
RENDER_H = SCREEN_HEIGHT // RENDER_SCALE

screen = pg.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pg.RESIZABLE | pg.DOUBLEBUF | pg.SCALED,
)
pg.display.set_caption("HexForge FPS")
pg.mouse.set_visible(not MOUSE_GRAB)
pg.event.set_grab(MOUSE_GRAB)

render_surf = pg.Surface((RENDER_W, RENDER_H), 0, 32)
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

weapons = {"AK47": AK47(), "Glock19": Glock19(), "Knife": Knife(), "Grenade": Grenade()}
for name, w in weapons.items():
    if hasattr(w, 'apply_upgrades'):
        ups = game_state.get_upgrades(name) + game_state.get_upgrades("AK47")
        w.apply_upgrades(ups)
grenade_count = game_state.get_grenades()
weapons["Grenade"].ammo = grenade_count
weapons["Grenade"].reserve = grenade_count

current_weapon = "AK47"
bullets = []
grenades = []
thrown_grenades = []

def pick_enemy_spawns(px, py, count=8, min_dist=12.0, max_dist=30.0):
    floor_tiles = game_map.get_floor_tiles()
    random.shuffle(floor_tiles)
    near = []
    far = []
    for tx, ty in floor_tiles:
        dx = (tx + 0.5) - px
        dy = (ty + 0.5) - py
        dist = math.hypot(dx, dy)
        if len(near) < count and min_dist <= dist <= max_dist:
            near.append((tx, ty))
        elif len(far) < count and dist > min_dist:
            far.append((tx, ty))
    picks = near
    if len(picks) < count:
        picks += far[:count - len(picks)]
    random.shuffle(picks)
    return picks[:count]


def spawn_targets():
    global targets
    targets = []
    for i, (tx, ty) in enumerate(pick_enemy_spawns(px, py, 8)):
        targets.append(Target(tx + 0.5, ty + 0.5, i, wave=wave))


spawn_targets()

prev_ammo_str = None
prev_reserve_str = None
prev_fps_str = None
cached_ammo_surf = None
cached_reserve_surf = None
cached_fps_surf = None
cached_weapon_name = None
cached_weapon_surf = None

tex_cols_np = np.array([
    pg.surfarray.array3d(get_texture(name))
    for name in TEXTURE_NAMES
], dtype=np.uint8)

floor_cols_np = pg.surfarray.array3d(get_texture("cobblestone")).astype(np.uint8)
ceil_cols_np = pg.surfarray.array3d(get_texture("concrete")).astype(np.uint8)
grass_cols_np = pg.surfarray.array3d(get_texture("grass")).astype(np.uint8)
water_cols_np = pg.surfarray.array3d(get_texture("water")).astype(np.uint8)

font = pg.font.SysFont("consolas", 22)
font_small = pg.font.SysFont("consolas", 16)
font_big = pg.font.SysFont("segoeui", 28, bold=True)
font_tiny = pg.font.SysFont("consolas", 13)
reserve_lbl = font_small.render("reserve", True, (140, 140, 140))

TAN_HALF_FOV = math.tan(math.radians(FOV / 2))
TAN_HALF_AIM_FOV = math.tan(math.radians(AIM_FOV / 2))
ray_offsets = [math.atan((2 * i / RENDER_W - 1) * TAN_HALF_FOV) for i in range(RENDER_W)]
ray_cos = np.cos(ray_offsets)
ray_sin = np.sin(ray_offsets)
aim_ray_offsets = [math.atan((2 * i / RENDER_W - 1) * TAN_HALF_AIM_FOV) for i in range(RENDER_W)]
aim_ray_cos = np.cos(aim_ray_offsets)
aim_ray_sin = np.sin(aim_ray_offsets)

mm_base = game_map.minimap(1)

impact_particles = []


class ImpactParticle:
    def __init__(self, x, y, z, vx, vy, vz, color, life=0.4):
        self.x = x
        self.y = y
        self.z = z
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.color = color
        self.life = life
        self.max_life = life
        self.gravity = 500.0
        self.size = random.uniform(1.0, 3.0)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.vz -= self.gravity * dt
        if self.z < 0:
            self.z = 0
            self.vz *= -0.3
            self.vx *= 0.5
            self.vy *= 0.5
        self.life -= dt
        return self.life > 0

    def draw(self, surf, px, py, pdx, pdy, fov, w, h):
        dx = self.x - px
        dy = self.y - py
        dist = math.hypot(dx, dy)
        if dist < 0.3:
            return
        angle_to = math.atan2(dy, dx)
        diff = angle_to - math.atan2(pdy, pdx)
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        half_fov = math.radians(fov / 2)
        if abs(diff) > half_fov + 0.2:
            return
        screen_x = int((diff / half_fov) * (w // 2) + w // 2)
        height_scale = h / (dist * 1.5)
        z_offset = int(self.z * height_scale)
        screen_y = h // 2 + z_offset
        if screen_x < 0 or screen_x >= w:
            return
        alpha = int(255 * (self.life / self.max_life))
        size = max(1, int(self.size * height_scale * 0.15))
        c = self.color
        pg.draw.circle(surf, (c[0] * alpha // 255, c[1] * alpha // 255, c[2] * alpha // 255),
                       (screen_x, screen_y), size)


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
        self.trail = []
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

        self.trail.append((self.x, self.y, self.z))
        if len(self.trail) > 20:
            self.trail.pop(0)

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

    def draw(self, surf, px, py, pdx, pdy, fov, w, h):
        if self.exploded:
            progress = 1 - (self.explosion_timer / 0.4)
            for r in range(int(60 * (1 - progress)), 0, -3):
                dx_screen, dy_screen = self._project(self.x, self.y, px, py, pdx, pdy, fov, w, h)
                if dx_screen is not None:
                    c_val = max(0, int(255 * (1 - progress)))
                    color = (c_val, int(c_val * 0.6), int(c_val * 0.2))
                    pg.draw.circle(surf, color, (dx_screen, dy_screen), max(1, r // 4))
            return

        for tx, ty, tz in self.trail:
            sx, sy = self._project(tx, ty, px, py, pdx, pdy, fov, w, h)
            if sx is not None:
                pg.draw.circle(surf, (100, 100, 110), (sx, sy), 1)

        sx, sy = self._project(self.x, self.y, px, py, pdx, pdy, fov, w, h)
        if sx is not None:
            pg.draw.circle(surf, (70, 85, 55), (sx, sy), 5)
            pg.draw.circle(surf, (50, 60, 40), (sx, sy), 3)
            fuse_glow = int(200 * (self.fuse / GRENADE_FUSE))
            pg.draw.circle(surf, (fuse_glow, fuse_glow // 3, 0), (sx, sy - 5), 2)

    def _project(self, wx, wy, px, py, pdx, pdy, fov, w, h):
        dx = wx - px
        dy = wy - py
        dist = math.hypot(dx, dy)
        if dist < 0.1:
            return None, None
        angle_to = math.atan2(dy, dx)
        diff = angle_to - math.atan2(pdy, pdx)
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        half_fov = math.radians(fov / 2)
        if abs(diff) > half_fov + 0.3:
            return None, None
        screen_x = int((diff / half_fov) * (w // 2) + w // 2)
        height_scale = h / (dist * 1.5)
        screen_y = h // 2 - int(self.z * height_scale) // 2
        return screen_x, screen_y


def emit_impact(x, y, count=12):
    for _ in range(count):
        angle_p = random.uniform(0, math.pi * 2)
        speed = random.uniform(20, 80)
        vz = random.uniform(30, 120)
        color = random.choice([(180, 160, 140), (160, 140, 120), (200, 180, 160), (140, 130, 110)])
        impact_particles.append(ImpactParticle(
            x, y, 0,
            math.cos(angle_p) * speed,
            math.sin(angle_p) * speed,
            vz, color, random.uniform(0.2, 0.6)
        ))


def cast_ray(ray_angle):
    dir_x = math.cos(ray_angle)
    dir_y = math.sin(ray_angle)
    map_x = int(px)
    map_y = int(py)
    delta_dist_x = 1e30 if dir_x == 0 else abs(1 / dir_x)
    delta_dist_y = 1e30 if dir_y == 0 else abs(1 / dir_y)
    if dir_x < 0:
        step_x = -1
        side_dist_x = (px - map_x) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (map_x + 1.0 - px) * delta_dist_x
    if dir_y < 0:
        step_y = -1
        side_dist_y = (py - map_y) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (map_y + 1.0 - py) * delta_dist_y
    hit = False
    side = 0
    steps = 0
    while not hit and steps < 64:
        steps += 1
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1
        if map_x < 0 or map_x >= game_map.width or map_y < 0 or map_y >= game_map.height:
            return None
        if game_map.grid[map_y][map_x] == 1:
            hit = True
    if not hit:
        return None
    if side == 0:
        perp_dist = (map_x - px + (1 - step_x) / 2) / dir_x
    else:
        perp_dist = (map_y - py + (1 - step_y) / 2) / dir_y
    if perp_dist < 0.01:
        perp_dist = 0.01
    if side == 0:
        wall_x = py + perp_dist * dir_y
    else:
        wall_x = px + perp_dist * dir_x
    wall_x -= math.floor(wall_x)
    tex_id = game_map.get_tex_id(map_x, map_y)
    return perp_dist, side, wall_x, tex_id, dir_x, dir_y, map_x, map_y


def render_floor_ceil(surf, w, h, use_ray_cos, use_ray_sin, use_tan_half_fov):
    half_h = h // 2
    arr = pg.surfarray.pixels3d(surf)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    cos_a_f = float(cos_a)
    sin_a_f = float(sin_a)

    floor_dir_x = (cos_a_f * use_ray_cos - sin_a_f * use_ray_sin).astype(np.float64)
    floor_dir_y = (sin_a_f * use_ray_cos + cos_a_f * use_ray_sin).astype(np.float64)

    for is_floor, col_data_np, scale in (
        (True, floor_cols_np, 1.5),
        (False, ceil_cols_np, 1.2),
    ):
        if is_floor:
            ys = np.arange(half_h + 1, h)
        else:
            ys = np.arange(0, half_h)
        if len(ys) == 0:
            continue
        p = (ys - half_h).astype(np.float64)
        abs_p = np.abs(p)
        pos_z = PLAYER_HEIGHT + player_z + pitch * (half_h - abs_p) / half_h
        row_distance = pos_z / abs_p / use_tan_half_fov

        rx = px + row_distance[:, np.newaxis] * floor_dir_x[np.newaxis, :]
        ry = py + row_distance[:, np.newaxis] * floor_dir_y[np.newaxis, :]

        tex_x = (rx * scale % TEX_SIZE).astype(np.int32)
        tex_y = (ry * scale % TEX_SIZE).astype(np.int32)

        pixels = col_data_np[tex_x, tex_y]

        fog = np.minimum(1.0, row_distance * 0.045)[:, np.newaxis, np.newaxis]
        fog_factor = 1.0 - fog

        block = np.clip(
            pixels * fog_factor + np.array([25.0, 22.0, 28.0]) * fog,
            0, 255
        ).astype(np.uint8)

        arr[:, ys] = block.transpose(1, 0, 2)


def render_3d(surf, w, h):
    depth = [float('inf')] * w
    arr = pg.surfarray.pixels3d(surf)
    half_h = h // 2

    if aiming:
        use_ray_offsets = aim_ray_offsets
        use_ray_cos = aim_ray_cos
        use_ray_sin = aim_ray_sin
        use_tan_half_fov = TAN_HALF_AIM_FOV
    else:
        use_ray_offsets = ray_offsets
        use_ray_cos = ray_cos
        use_ray_sin = ray_sin
        use_tan_half_fov = TAN_HALF_FOV

    render_floor_ceil(surf, w, h, use_ray_cos, use_ray_sin, use_tan_half_fov)
    for ray in range(w):
        ray_angle = angle + use_ray_offsets[ray]
        result = cast_ray(ray_angle)
        if result is None:
            continue
        perp_dist, side, wall_x, tex_id, dir_x, dir_y, map_x, map_y = result
        perp_dist *= use_ray_cos[ray]
        if perp_dist < 0.01:
            perp_dist = 0.01
        depth[ray] = perp_dist
        wall_h = int(h / perp_dist)
        wall_top = half_h - wall_h // 2 + int(pitch)
        wall_bot = wall_top + wall_h
        if wall_top >= wall_bot:
            continue
        if wall_top < 0:
            wall_top = 0
        if wall_bot > h:
            wall_bot = h
        shade = 0.6 if side == 1 else 1.0
        dist_factor = max(0.1, 1 - perp_dist * 0.03)
        light = shade * dist_factor
        tex_id = tex_id % len(tex_cols_np)
        tex_x = int(wall_x * TEX_SIZE)
        if side == 0 and dir_x > 0:
            tex_x = TEX_SIZE - tex_x - 1
        if side == 1 and dir_y < 0:
            tex_x = TEX_SIZE - tex_x - 1
        fog = min(1, perp_dist * 0.035)
        fog_factor = max(0, 1 - fog)
        num_px = wall_bot - wall_top
        step = TEX_SIZE / wall_h
        tex_pos_arr = np.arange(num_px, dtype=np.float64) * step
        tex_pos_arr += (wall_top - half_h + wall_h // 2) * step
        tex_y_arr = np.clip(tex_pos_arr.astype(np.int32), 0, TEX_SIZE - 1)
        col_data = tex_cols_np[tex_id % len(tex_cols_np), tex_x]
        pixels = col_data[tex_y_arr].astype(np.float64)
        pixels *= light
        pixels += np.array([30.0, 28.0, 35.0]) * fog
        pixels *= fog_factor
        arr[ray, wall_top:wall_bot] = np.clip(pixels, 0, 255).astype(np.uint8)
    del arr
    return depth


def render_targets(surf, depth, w, h):
    half_h = h // 2
    visible = []
    for t in targets:
        info = t.get_screen_info(px, py, angle, display_fov, w, h)
        if info:
            visible.append((t, info))
    visible.sort(key=lambda v: v[1][4], reverse=True)
    for t, info in visible:
        sx, sy, sw, sh, dist = info
        if t.alive:
            base_color = (255, 80, 60) if t.hit_flash > 0 else (90, 160, 230)
        else:
            base_color = (55, 55, 55)
        head_r = max(2, int(sw * 0.35))
        body_w = sw
        body_h = int(sh * 0.65)
        body_y = sy + int(sh * 0.35)
        head_y = sy + head_r
        left = max(0, sx - body_w // 2)
        right = min(w, sx + body_w // 2)
        fog = min(1, dist * 0.03)
        fog_factor = max(0, 1 - fog)
        for col in range(left, right):
            if col < 0 or col >= w:
                continue
            if dist >= depth[col]:
                continue
            col_dist = abs(col - sx) / max(1, body_w // 2)
            shade = 1.0 - col_dist * 0.3
            if abs(col - sx) <= head_r:
                dh = head_r - abs(col - sx)
                for row in range(max(0, head_y - dh), min(h, head_y + dh)):
                    if dist < depth[col]:
                        c = base_color
                        s = shade * (1 - abs(row - head_y) / max(1, dh) * 0.2)
                        r = min(255, max(0, int(c[0] * s * fog_factor + 50 * fog)))
                        g = min(255, max(0, int(c[1] * s * fog_factor + 48 * fog)))
                        b = min(255, max(0, int(c[2] * s * fog_factor + 55 * fog)))
                        surf.set_at((col, int(row)), (r, g, b))
            if abs(col - sx) <= body_w // 2:
                for row in range(max(0, body_y), min(h, body_y + body_h)):
                    if dist < depth[col]:
                        c = base_color
                        arm_offset = int(body_w * 0.22)
                        if abs(col - sx) > body_w // 2 - arm_offset:
                            shade_arm = 0.6
                            c = (c[0] - 20, c[1] - 20, c[2] - 20)
                        else:
                            shade_arm = shade
                        s = shade_arm * (1 - (row - body_y) / max(1, body_h) * 0.12)
                        r = min(255, max(0, int(c[0] * s * fog_factor + 50 * fog)))
                        g = min(255, max(0, int(c[1] * s * fog_factor + 48 * fog)))
                        b = min(255, max(0, int(c[2] * s * fog_factor + 55 * fog)))
                        surf.set_at((col, row), (r, g, b))
        if t.alive and (0 <= sx < w and dist < depth[sx]):
            cx, cy = sx, body_y - int(sh * 0.05)
            hp_pct = t.hp / t.max_hp
            if hp_pct > 0.5:
                dot_c = (0, 255, 80)
            elif hp_pct > 0.25:
                dot_c = (255, 200, 50)
            else:
                dot_c = (255, 40, 40)
            pg.draw.circle(surf, dot_c, (cx, cy), max(1, int(sw * 0.15)), 1)
            pg.draw.circle(surf, dot_c, (cx, cy), max(1, int(sw * 0.08)), 1)


def apply_vignette(surf, w, h):
    arr = pg.surfarray.pixels3d(surf)
    cx, cy = w / 2, h / 2
    dx = (np.arange(w, dtype=np.float64) - cx) / cx
    dy = (np.arange(h, dtype=np.float64) - cy) / cy
    vig = 1.0 - (dx[:, np.newaxis] ** 2 + dy[np.newaxis, :] ** 2) * 0.35
    np.maximum(vig, 0.4, out=vig)
    arr[:] = np.clip(arr * vig[:, :, np.newaxis], 0, 255).astype(np.uint8)
    del arr


def handle_input(dt):
    global px, py, pdx, pdy, angle, pitch, current_weapon
    global player_z, player_vz, on_ground, aiming

    keys = pg.key.get_pressed()
    speed = PLAYER_SPEED * dt
    if game_map.is_water(px, py):
        speed *= 0.5
    moving = False

    dx, dy = 0.0, 0.0
    if keys[CONTROLS["FORWARD"]]:
        dx += pdx * speed
        dy += pdy * speed
        moving = True
    if keys[CONTROLS["BACKWARD"]]:
        dx -= pdx * speed
        dy -= pdy * speed
        moving = True
    if keys[CONTROLS["LEFT"]]:
        dx -= pdy * speed
        dy += pdx * speed
        moving = True
    if keys[CONTROLS["RIGHT"]]:
        dx += pdy * speed
        dy -= pdx * speed
        moving = True

    nx, ny = px + dx, py + dy
    if not game_map.is_wall(nx, ny):
        px, py = nx, ny
    elif not game_map.is_wall(nx, py):
        px = nx
    elif not game_map.is_wall(px, ny):
        py = ny

    if keys[CONTROLS["JUMP"]] and on_ground:
        player_vz = JUMP_FORCE
        on_ground = False

    player_vz -= GRAVITY * dt
    player_z += player_vz * dt
    if player_z <= 0:
        player_z = 0
        player_vz = 0
        on_ground = True

    aiming = pg.mouse.get_pressed()[2]

    rel_x, rel_y = pg.mouse.get_rel()
    if MOUSE_GRAB:
        angle -= rel_x * MOUSE_SENSITIVITY
        pitch -= rel_y * MOUSE_SENSITIVITY * 8
        pitch = max(-200, min(200, pitch))

    pdx = math.cos(angle)
    pdy = math.sin(angle)

    if keys[CONTROLS["WEAPON_1"]] and game_state.has_weapon("AK47"):
        current_weapon = "AK47"
    if keys[CONTROLS["WEAPON_2"]] and game_state.has_weapon("Glock19"):
        current_weapon = "Glock19"
    if keys[CONTROLS["WEAPON_3"]] and game_state.has_weapon("Knife"):
        current_weapon = "Knife"
    if keys[CONTROLS["WEAPON_4"]] and game_state.has_weapon("Grenade"):
        current_weapon = "Grenade"

    if keys[CONTROLS["INTERACT"]]:
        look_x = px + pdx * 1.5
        look_y = py + pdy * 1.5
        game_map.try_open_door(look_x, look_y)

    gun = weapons[current_weapon]

    if pg.mouse.get_pressed()[0]:
        if current_weapon == "Grenade":
            if gun.shoot():
                if game_state.use_grenade():
                    throw = GrenadeProjectile(px, py, angle, gun.damage)
                    thrown_grenades.append(throw)
                    gun.ammo = game_state.get_grenades()
                    sound.play_grenade_throw()
        elif current_weapon == "Knife":
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
        elif current_weapon == "Glock19":
            if gun.shoot():
                bullets.append(Bullet(px, py, angle))
                sound.play_pistol()
        else:
            if gun.shoot():
                bullets.append(Bullet(px, py, angle))
                sound.play_gunshot()

    if keys[CONTROLS["RELOAD"]]:
        gun.start_reload()

    gun.update(dt, moving)


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


def draw_hands(surf, w, h, moving, dt):
    gun = weapons[current_weapon]
    bob = gun.bob_offset if hasattr(gun, 'bob_offset') else 0
    kickback = gun.kickback if hasattr(gun, 'kickback') else 0

    t = pg.time.get_ticks() * 0.001
    arm_sway_x = math.sin(t * 2.5) * (4 if moving else 1)
    arm_sway_y = math.sin(t * 3.0) * (3 if moving else 1) + kickback * 2

    hand_x = w // 2 + 60 + arm_sway_x
    hand_y = h - 30 + arm_sway_y

    skin = (210, 175, 140)
    skin_dark = (180, 145, 110)

    pg.draw.polygon(surf, skin, [
        (hand_x - 18, hand_y + 5),
        (hand_x + 18, hand_y + 5),
        (hand_x + 14, hand_y + 30),
        (hand_x - 14, hand_y + 30),
    ])
    pg.draw.polygon(surf, skin_dark, [
        (hand_x - 14, hand_y + 28),
        (hand_x + 14, hand_y + 28),
        (hand_x + 12, hand_y + 45),
        (hand_x - 12, hand_y + 45),
    ])

    for i in range(4):
        fx = hand_x - 10 + i * 7
        pg.draw.polygon(surf, skin, [
            (fx, hand_y - 2),
            (fx + 5, hand_y - 2),
            (fx + 5, hand_y + 8),
            (fx, hand_y + 8),
        ])

    pg.draw.polygon(surf, skin, [
        (hand_x - 14, hand_y - 2),
        (hand_x - 8, hand_y - 2),
        (hand_x - 8, hand_y + 8),
        (hand_x - 14, hand_y + 6),
    ])

    thumb_x = hand_x + 16
    pg.draw.polygon(surf, skin, [
        (thumb_x, hand_y),
        (thumb_x + 8, hand_y - 4),
        (thumb_x + 9, hand_y + 4),
        (thumb_x, hand_y + 8),
    ])


def draw_hud(surf, w, h):
    global prev_ammo_str, prev_reserve_str, prev_fps_str, cached_weapon_name, cached_weapon_surf, cached_ammo_surf, cached_reserve_surf, cached_fps_surf

    cx, cy = w // 2, h // 2

    gun = weapons[current_weapon]

    if current_weapon != "Knife":
        if not gun.reloading:
            pg.draw.line(surf, COLORS["CROSSHAIR"], (cx - 10, cy), (cx + 10, cy), 2)
            pg.draw.line(surf, COLORS["CROSSHAIR"], (cx, cy - 10), (cx, cy + 10), 2)
            pg.draw.circle(surf, COLORS["CROSSHAIR"], (cx, cy), 2, 1)
    else:
        pg.draw.circle(surf, COLORS["CROSSHAIR"], (cx, cy), 8, 1)

    if current_weapon != "Knife":
        draw_hands(surf, w, h, False, 0)

    gun.draw(surf, w, h)

    if current_weapon != "Knife":
        if current_weapon == "Grenade":
            ammo_str = f"x{game_state.get_grenades()}"
        else:
            ammo_str = f"{gun.ammo}/{gun.mag_size}"
        if ammo_str != prev_ammo_str:
            prev_ammo_str = ammo_str
            cached_ammo_surf = font.render(ammo_str, True, COLORS["HUD_TEXT"])
        surf.blit(cached_ammo_surf, (w - 150, h - 65))

        if current_weapon != "Grenade":
            reserve_str = str(gun.reserve)
            if reserve_str != prev_reserve_str:
                prev_reserve_str = reserve_str
                cached_reserve_surf = font.render(reserve_str, True, (180, 180, 180))
            surf.blit(cached_reserve_surf, (w - 150, h - 42))
            surf.blit(reserve_lbl, (w - 150, h - 28))

    fps_str = f"{int(clock.get_fps())} FPS"
    if fps_str != prev_fps_str:
        prev_fps_str = fps_str
        cached_fps_surf = font.render(fps_str, True, (0, 255, 0))
    surf.blit(cached_fps_surf, (12, 12))

    if current_weapon != cached_weapon_name:
        cached_weapon_name = current_weapon
        cached_weapon_surf = font_big.render(current_weapon, True, (230, 150, 40))
    surf.blit(cached_weapon_surf, (w // 2 - cached_weapon_surf.get_width() // 2, 16))

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

    weapon_slots = [
        ("1", "AK47", game_state.has_weapon("AK47")),
        ("2", "Glock19", game_state.has_weapon("Glock19")),
        ("3", "Knife", game_state.has_weapon("Knife")),
        ("4", "Grenade", game_state.has_weapon("Grenade")),
    ]
    slot_x = w - 200
    slot_y = 16
    for key, wname, owned in weapon_slots:
        if not owned:
            continue
        active = current_weapon == wname
        slot_bg = (50, 50, 60) if active else (30, 30, 38)
        slot_border = (230, 150, 40) if active else (60, 60, 70)
        slot_rect = pg.Rect(slot_x, slot_y, 46, 46)
        pg.draw.rect(surf, slot_bg, slot_rect, border_radius=6)
        pg.draw.rect(surf, slot_border, slot_rect, 2, border_radius=6)
        kn = font_tiny.render(key, True, (230, 150, 40) if active else (140, 140, 150))
        surf.blit(kn, (slot_x + 4, slot_y + 4))
        nn = font_tiny.render(wname[:4], True, (255, 255, 255) if active else (100, 100, 110))
        surf.blit(nn, (slot_x + 4, slot_y + 22))
        slot_x += 54

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

    if current_weapon == "Knife":
        melee_hint = font_tiny.render("CLOSE RANGE - Click to stab", True, (140, 140, 150))
        surf.blit(melee_hint, (w // 2 - melee_hint.get_width() // 2, h - 75))
    elif current_weapon == "Grenade":
        g_count = game_state.get_grenades()
        grenade_hint = font_tiny.render(f"THROW - {g_count} grenades left", True, (140, 140, 150))
        surf.blit(grenade_hint, (w // 2 - grenade_hint.get_width() // 2, h - 75))

    money = game_state.get_money()
    money_txt = font.render(f"${money}", True, (230, 200, 50))
    surf.blit(money_txt, (w - 150, h - 85))


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
    global player_hp, wave, damage_flash, death_timer
    running = True
    current_weapon = "AK47"

    while running:
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.05:
            dt = 0.05

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    running = False
                if event.key == pg.K_1 and game_state.has_weapon("AK47"):
                    current_weapon = "AK47"
                if event.key == pg.K_2 and game_state.has_weapon("Glock19"):
                    current_weapon = "Glock19"
                if event.key == pg.K_3 and game_state.has_weapon("Knife"):
                    current_weapon = "Knife"
                if event.key == pg.K_4 and game_state.has_weapon("Grenade"):
                    current_weapon = "Grenade"

        handle_input(dt)

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

        depth = render_3d(render_surf, RENDER_W, RENDER_H)
        render_targets(render_surf, depth, RENDER_W, RENDER_H)
        apply_vignette(render_surf, RENDER_W, RENDER_H)

        pg.transform.scale(render_surf, (SCREEN_WIDTH, SCREEN_HEIGHT), screen)

        for b in bullets:
            b.draw(screen, px, py, pdx, pdy, display_fov)

        for t in targets:
            for eb in t.enemy_bullets:
                eb.draw(screen, px, py, pdx, pdy, display_fov)

        for g in thrown_grenades:
            g.draw(screen, px, py, pdx, pdy, display_fov, SCREEN_WIDTH, SCREEN_HEIGHT)

        impact_particles = [p for p in impact_particles if p.update(dt)]
        for p in impact_particles:
            p.draw(screen, px, py, pdx, pdy, display_fov, SCREEN_WIDTH, SCREEN_HEIGHT)

        if damage_flash > 0:
            flash_alpha = int(180 * (damage_flash / 0.3))
            flash_surf = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
            flash_surf.fill((255, 0, 0, flash_alpha))
            screen.blit(flash_surf, (0, 0))

        if player_hp <= 0:
            death_surf = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
            death_surf.fill((0, 0, 0, 160))
            screen.blit(death_surf, (0, 0))
            death_txt = font_big.render("YOU DIED", True, (220, 40, 40))
            screen.blit(death_txt, (SCREEN_WIDTH // 2 - death_txt.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        draw_hud(screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        if aiming:
            draw_scope(screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        pg.display.flip()

    pg.quit()


if __name__ == "__main__":
    run()
