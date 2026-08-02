import math
import os
import sys
import random
import pygame

TEX_SIZE = 256

_PRIME_X = 1619
_PRIME_Y = 31337
_PRIME_SEED = 69763


def _hash(ix, iy):
    n = ix * _PRIME_X + iy * _PRIME_Y + _PRIME_SEED
    n = (n << 13) ^ n
    return (1.0 - ((n * (n * n * 15731 + 789221) + 1376312589) & 0x7fffffff) / 1073741824.0)


def _smooth_noise(x, y):
    ix = math.floor(x)
    iy = math.floor(y)
    fx = x - ix
    fy = y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    v00 = _hash(ix, iy)
    v10 = _hash(ix + 1, iy)
    v01 = _hash(ix, iy + 1)
    v11 = _hash(ix + 1, iy + 1)
    return v00 + (v10 - v00) * fx + (v01 - v00) * fy + (v11 - v10 - v01 + v00) * fx * fy


def fbm(x, y, octaves=5, lacunarity=2.0, gain=0.5):
    value = 0.0
    amplitude = 1.0
    frequency = 1.0
    max_val = 0.0
    for _ in range(octaves):
        value += amplitude * _smooth_noise(x * frequency, y * frequency)
        max_val += amplitude
        amplitude *= gain
        frequency *= lacunarity
    return value / max_val


def _norm(c):
    return max(0, min(255, int(c)))


def _clamp_pixel(surf, x, y, r, g, b):
    w, h = surf.get_size()
    if 0 <= x < w and 0 <= y < h:
        surf.set_at((x, y), (_norm(r), _norm(g), _norm(b)))


def _brick_pattern(x, y, brick_w, brick_h, mortar):
    row = y // brick_h
    col = x // brick_w
    offset_x = (row & 1) * (brick_w // 2)
    lx = (x + offset_x) % brick_w
    ly = y % brick_h
    return lx < brick_w - mortar and ly < brick_h - mortar, lx, ly


def brick():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    scale = TEX_SIZE / 256.0
    brick_w = int(64 * scale)
    brick_h = int(28 * scale)
    mortar = max(1, int(3 * scale))

    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            is_brick, lx, ly = _brick_pattern(x, y, brick_w, brick_h, mortar)
            if not is_brick:
                n = fbm(x * 0.4, y * 0.4, 3) * 0.3 + 0.2
                c = int(65 + n * 40 + fbm(x * 0.1, y * 0.1, 2) * 10)
                _clamp_pixel(surf, x, y, c, c - 2, c - 5)
                continue
            n1 = fbm(x * 0.03 + 5.3, y * 0.03 + 1.7, 4, 2.2, 0.55)
            n2 = fbm(x * 0.12 - 3.1, y * 0.12 + 7.5, 3, 2.0, 0.5) * 0.5
            n3 = fbm(x * 0.5 + 11.3, y * 0.5 - 4.7, 2, 2.0, 0.5) * 0.15

            base_r = 150 + n1 * 60 + n2 * 20 + n3 * 30
            base_g = 65 + n1 * 35 + n2 * 15 + n3 * 10
            base_b = 30 + n1 * 20 + n2 * 10 + n3 * 5

            edge = min(lx, brick_w - mortar - lx, ly, brick_h - mortar - ly)
            edge_factor = max(0, 1 - edge / (brick_w * 0.15))
            darkening = 1 - edge_factor * 0.3
            highlight = 1 + max(0, 1 - edge / (brick_w * 0.08)) * 0.15 if ly < brick_h * 0.15 else 1

            r = base_r * darkening * highlight
            g = base_g * darkening * highlight
            b = base_b * darkening * highlight

            grain = (fbm(x * 0.8 + 3.3, y * 0.8 + 9.1, 2) - 0.5) * 8
            _clamp_pixel(surf, x, y, r + grain, g + grain * 0.6, b + grain * 0.4)
    return surf


def stone():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    scale = TEX_SIZE / 256.0
    block = int(56 * scale)
    gap = max(1, int(2 * scale))

    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            gx = (x // block) & 3
            gy = (y // block) & 3
            lx = x % block
            ly = y % block

            if lx < gap or ly < gap or lx >= block - gap or ly >= block - gap:
                _clamp_pixel(surf, x, y, 50, 48, 45)
                continue

            ox = _hash(gx * 7 + 3, gy * 13 + 7) * 10
            oy = _hash(gx * 11 + 5, gy * 5 + 11) * 10
            n1 = fbm((x + ox) * 0.04, (y + oy) * 0.04, 5, 2.3, 0.55)
            n2 = fbm((x + ox) * 0.15, (y + oy) * 0.15, 3, 2.0, 0.5)

            base = 100 + n1 * 60 + n2 * 15
            r = base + n2 * 5
            g = base + n2 * 3
            b = base - 5 + n2 * 2

            crack = fbm(x * 0.08, y * 0.08, 2) * 0.5 + 0.5
            if crack > 0.85:
                f = (crack - 0.85) * 6
                r -= f * 40
                g -= f * 35
                b -= f * 30

            spec = fbm((x + ox) * 0.3, (y + oy) * 0.3, 2) * 0.5 + 0.5
            if spec > 0.92:
                s = (spec - 0.92) * 12
                r += s * 20
                g += s * 20
                b += s * 25

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


def metal():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            n1 = fbm(x * 0.025, y * 0.025, 5, 2.2, 0.55)
            n2 = fbm(x * 0.08, y * 0.08, 4, 2.0, 0.5)
            n3 = fbm(x * 0.3 - 5.0, y * 0.3 + 3.0, 2, 2.0, 0.5)

            base = 130 + n1 * 70 + n2 * 30
            r = base + n3 * 15 + 5
            g = base + n3 * 10 + 3
            b = base + n3 * 5

            streak = fbm(x * 0.01, y * 0.04, 3, 2.0, 0.5) * 0.5 + 0.5
            if streak > 0.7:
                f = (streak - 0.7) * 3
                r += f * 15
                g += f * 12
                b += f * 10

            scratch = fbm(x * 0.5, y * 0.5, 2) * 0.5 + 0.5
            if scratch > 0.95:
                r += 30
                g += 28
                b += 25

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


def wood():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            nx = x / TEX_SIZE
            ny = y / TEX_SIZE

            ring_noise = fbm(nx * 0.5 + 2.3, ny * 0.5 - 1.4, 3, 2.0, 0.5) * 0.15
            dist = abs(nx - 0.5 + ring_noise) * 2
            ring = math.sin(dist * math.pi * 12 + fbm(nx * 3, ny * 3, 2) * 0.5)
            ring = ring * 0.5 + 0.5
            ring = ring ** 0.6

            grain_n = fbm(x * 0.3 + 5.0, y * 0.1 + 1.0, 4, 2.2, 0.5)
            base_r = 130 + ring * 50 + grain_n * 20
            base_g = 80 + ring * 30 + grain_n * 10
            base_b = 35 + ring * 15 + grain_n * 5

            knot = fbm(x * 0.05 - 3.0, y * 0.05 + 2.0, 3) * 0.5 + 0.5
            if knot > 0.8 and abs(nx - 0.5) < 0.2 and abs(ny - 0.5) < 0.2:
                kf = (knot - 0.8) * 5
                base_r -= kf * 50
                base_g -= kf * 35
                base_b -= kf * 15

            grain_fine = (fbm(x * 0.8, y * 0.8, 2) - 0.5) * 10
            r = base_r + grain_fine
            g = base_g + grain_fine * 0.6
            b = base_b + grain_fine * 0.3

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


def concrete():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            n1 = fbm(x * 0.04, y * 0.04, 5, 2.3, 0.55)
            n2 = fbm(x * 0.15, y * 0.15, 3, 2.0, 0.5)
            n3 = fbm(x * 0.5, y * 0.5, 2, 2.0, 0.5)

            base = 135 + n1 * 45 + n2 * 20
            r = base + n3 * 8
            g = base + n3 * 6
            b = base + n3 * 4

            patch = fbm(x * 0.03 - 2.0, y * 0.03 + 5.0, 3) * 0.5 + 0.5
            if patch > 0.75:
                pf = (patch - 0.75) * 4
                r += pf * 10
                g += pf * 8
                b += pf * 5

            crack = fbm(x * 0.06 + 7.0, y * 0.06 - 3.0, 3) * 0.5 + 0.5
            if crack > 0.88:
                cf = (crack - 0.88) * 8
                r -= cf * 30
                g -= cf * 28
                b -= cf * 25

            pebble = fbm(x * 0.4 + 1.0, y * 0.4 + 9.0, 2) * 0.5 + 0.5
            if pebble > 0.92:
                sf = (pebble - 0.92) * 12
                r += sf * 15
                g += sf * 13
                b += sf * 10

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


def marble():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            n1 = fbm(x * 0.02, y * 0.02, 6, 2.3, 0.55)
            n2 = fbm(x * 0.06 + 5.0, y * 0.06 + 3.0, 4, 2.0, 0.5)
            n3 = fbm(x * 0.012 - 7.0, y * 0.012 + 2.0, 3, 2.5, 0.5)

            vein = math.sin(n1 * math.pi * 4 + n2 * 2 + n3 * 3) * 0.5 + 0.5
            vein = vein ** 1.5

            base = 180 + vein * 50
            r = base + n2 * 15
            g = base + n2 * 8
            b = base + 10 + n2 * 12

            detail = fbm(x * 0.3, y * 0.3, 2) * 0.5 + 0.5
            if detail > 0.85:
                df = (detail - 0.85) * 6
                r += df * 20
                g += df * 15
                b += df * 25

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


def cobblestone():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    scale = TEX_SIZE / 256.0
    stone_size = int(40 * scale)

    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            gx = x // stone_size
            gy = y // stone_size
            ox = _hash(gx * 5 + 1, gy * 7 + 3) * 0.35 + 0.5
            oy = _hash(gx * 9 + 2, gy * 3 + 5) * 0.35 + 0.5

            cx = (gx + ox) * stone_size
            cy = (gy + oy) * stone_size
            rx = stone_size * 0.4 + _hash(gx * 11, gy * 13) * 0.15 * stone_size
            ry = stone_size * 0.4 + _hash(gx * 17, gy * 19) * 0.15 * stone_size

            dx = (x - cx) / rx
            dy = (y - cy) / ry
            in_stone = dx * dx + dy * dy < 1.0

            if not in_stone:
                n = fbm(x * 0.3, y * 0.3, 3) * 0.5 + 0.5
                c = int(55 + n * 30)
                _clamp_pixel(surf, x, y, c, c - 2, c - 4)
                continue

            n1 = fbm(x * 0.04 + 2.0, y * 0.04 + 5.0, 5, 2.2, 0.55)
            n2 = fbm(x * 0.15, y * 0.15, 3, 2.0, 0.5)

            dist_from_center = math.sqrt(dx * dx + dy * dy)
            edge_shade = 1 - max(0, dist_from_center) * 0.35

            base = 110 + n1 * 60 + n2 * 15
            r = base * edge_shade + n2 * 8
            g = base * edge_shade + n2 * 5
            b = base * edge_shade - 5 + n2 * 3

            moss = fbm(x * 0.05 - 4.0, y * 0.05 + 8.0, 4) * 0.5 + 0.5
            if moss > 0.8 and dist_from_center > 0.5:
                mf = (moss - 0.8) * 5 * (dist_from_center - 0.5) * 2
                g += mf * 30
                r -= mf * 10

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


def sandstone():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            n1 = fbm(x * 0.03, y * 0.03, 5, 2.3, 0.55)
            n2 = fbm(x * 0.1, y * 0.1, 3, 2.0, 0.5)
            n3 = fbm(x * 0.4, y * 0.4, 2, 2.0, 0.5)

            base_r = 170 + n1 * 40 + n2 * 15
            base_g = 140 + n1 * 35 + n2 * 12
            base_b = 80 + n1 * 30 + n2 * 10

            layer = fbm(x * 0.02 + 3.0, y * 0.02 - 2.0, 3, 2.0, 0.5) * 0.5 + 0.5
            if layer > 0.6:
                lf = (layer - 0.6) * 2.5
                base_r += lf * 15
                base_g += lf * 10
                base_b -= lf * 5

            grain = (n3 - 0.5) * 15
            r = base_r + grain
            g = base_g + grain * 0.8
            b = base_b + grain * 0.5

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


def grass():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            n1 = fbm(x * 0.03, y * 0.03, 5, 2.3, 0.55)
            n2 = fbm(x * 0.1 + 5.0, y * 0.1 + 3.0, 3, 2.0, 0.5)
            n3 = fbm(x * 0.4 + 1.0, y * 0.4 + 8.0, 2, 2.0, 0.5)

            r = 45 + n1 * 30 + n2 * 15
            g = 110 + n1 * 50 + n2 * 25 + n3 * 10
            b = 35 + n1 * 15 + n2 * 8

            blade = fbm(x * 0.8 + 11.0, y * 0.8 + 7.0, 2) * 0.5 + 0.5
            if blade > 0.85:
                f = (blade - 0.85) * 6
                g += f * 40
                r += f * 10

            dark = fbm(x * 0.05 + 3.0, y * 0.05 - 2.0, 3) * 0.5 + 0.5
            if dark > 0.7:
                df = (dark - 0.7) * 3
                r -= df * 15
                g -= df * 20
                b -= df * 10

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


def water():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            n1 = fbm(x * 0.02, y * 0.02, 4, 2.0, 0.5)
            n2 = fbm(x * 0.06 + 10.0, y * 0.06 + 5.0, 3, 2.0, 0.5)
            n3 = fbm(x * 0.15 + 3.0, y * 0.15 - 1.0, 2, 2.0, 0.5)

            r = 20 + n1 * 15 + n3 * 10
            g = 60 + n1 * 35 + n2 * 15 + n3 * 10
            b = 140 + n1 * 50 + n2 * 25 + n3 * 15

            wave = math.sin(x * 0.05 + n1 * 3.0) * 0.5 + 0.5
            r += wave * 10
            g += wave * 15
            b += wave * 20

            spec = fbm(x * 0.2 + 7.0, y * 0.2 + 3.0, 2) * 0.5 + 0.5
            if spec > 0.88:
                sf = (spec - 0.88) * 8
                r += sf * 40
                g += sf * 50
                b += sf * 60

            _clamp_pixel(surf, x, y, r, g, b)
    return surf


_texture_generators = {
    "brick": brick,
    "stone": stone,
    "metal": metal,
    "wood": wood,
    "concrete": concrete,
    "marble": marble,
    "cobblestone": cobblestone,
    "sandstone": sandstone,
    "grass": grass,
    "water": water,
}

TEXTURES = {}

def _cache_dir():
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), 'texture_cache')
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'texture_cache')


CACHE_DIR = _cache_dir()

def get_texture(name):
    if name not in TEXTURES:
        cached_path = os.path.join(CACHE_DIR, f'{name}.png')
        if os.path.exists(cached_path):
            surf = pygame.image.load(cached_path).convert()
        else:
            surf = _texture_generators[name]()
            os.makedirs(CACHE_DIR, exist_ok=True)
            pygame.image.save(surf, cached_path)
        TEXTURES[name] = surf
    return TEXTURES[name]

WEAPON_IMAGES = {}

def get_weapon_image(name):
    if name not in WEAPON_IMAGES:
        path = os.path.join(CACHE_DIR, f'{name}.png')
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
        else:
            surf = None
        WEAPON_IMAGES[name] = surf
    return WEAPON_IMAGES[name]

TEXTURE_NAMES = list(_texture_generators.keys())
