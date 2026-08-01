import math
import random
from textures import TEXTURE_NAMES

TILE_FLOOR = 0
TILE_WALL = 1
TILE_WATER = 2
TILE_GRASS = 3
TILE_DOOR = 4
TILE_STAIRS_UP = 5
TILE_STAIRS_DOWN = 6


class Door:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.open = False
        self.open_amount = 0.0
        self.speed = 3.0

    def update(self, dt):
        target = 1.0 if self.open else 0.0
        diff = target - self.open_amount
        if abs(diff) > 0.01:
            self.open_amount += math.copysign(self.speed * dt, diff)
            self.open_amount = max(0.0, min(1.0, self.open_amount))

    def toggle(self):
        self.open = not self.open

    def is_open(self):
        return self.open_amount > 0.8

    def blocks(self):
        return self.open_amount < 0.8


class Map:
    def __init__(self, width=100, height=100):
        self.width = width
        self.height = height
        self.grid = None
        self.tex_map = None
        self.floor_type = None
        self.doors = []
        self.stairs_up = []
        self.stairs_down = []
        self._generate()

    def _generate(self):
        self.grid = [[TILE_WALL for _ in range(self.width)] for _ in range(self.height)]
        self.tex_map = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.floor_type = [[TILE_FLOOR for _ in range(self.width)] for _ in range(self.height)]
        self.doors = []
        self.stairs_up = []
        self.stairs_down = []

        cx, cy = self.width // 2, self.height // 2
        self._carve(cx, cy)

        rooms = []
        rooms.append((cx, cy))
        for _ in range(150):
            x, y = random.choice(rooms)
            dx, dy = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            length = random.randint(8, 30)
            for _ in range(length):
                nx, ny = x + dx, y + dy
                if 3 < nx < self.width - 3 and 3 < ny < self.height - 3:
                    x, y = nx, ny
                    self._carve(x, y)
                    self._carve(x + dy, y + dx)
                    self._carve(x - dy, y - dx)
                    self._carve(x + 2 * dy, y + 2 * dx)
                    self._carve(x - 2 * dy, y - 2 * dx)
            rooms.append((x, y))

        for _ in range(40):
            rx = random.randint(4, self.width - 5)
            ry = random.randint(4, self.height - 5)
            rw = random.randint(5, 12)
            rh = random.randint(5, 12)
            for ddy in range(-rh // 2, rh // 2 + 1):
                for ddx in range(-rw // 2, rw // 2 + 1):
                    self._carve(rx + ddx, ry + ddy)
            rooms.append((rx, ry))

        self._add_doors(rooms)
        self._add_stairs()
        self._add_grass_patches()
        self._add_water_features()

        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] == TILE_WALL:
                    self.tex_map[y][x] = random.randint(0, len(TEXTURE_NAMES) - 1)

    def _carve(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = TILE_FLOOR
            self.tex_map[y][x] = 0
            self.floor_type[y][x] = TILE_FLOOR

    def _add_doors(self, rooms):
        door_count = 0
        for _ in range(40):
            x = random.randint(3, self.width - 4)
            y = random.randint(3, self.height - 4)
            if self.grid[y][x] != TILE_WALL:
                continue
            h_open = (self.grid[y][x - 1] == TILE_FLOOR and self.grid[y][x + 1] == TILE_FLOOR
                      and self.grid[y - 1][x] == TILE_WALL and self.grid[y + 1][x] == TILE_WALL)
            v_open = (self.grid[y - 1][x] == TILE_FLOOR and self.grid[y + 1][x] == TILE_FLOOR
                      and self.grid[y][x - 1] == TILE_WALL and self.grid[y][x + 1] == TILE_WALL)
            if h_open or v_open:
                self.grid[y][x] = TILE_DOOR
                self.floor_type[y][x] = TILE_DOOR
                self.doors.append(Door(x, y))
                door_count += 1
                if door_count >= 20:
                    break

    def _add_stairs(self):
        floor_tiles = [(x, y) for y in range(self.height) for x in range(self.width)
                       if self.grid[y][x] == TILE_FLOOR]
        if len(floor_tiles) < 10:
            return
        random.shuffle(floor_tiles)
        su = floor_tiles[0]
        self.stairs_up = [(su[0], su[1])]
        self.floor_type[su[1]][su[0]] = TILE_STAIRS_UP
        sd = floor_tiles[len(floor_tiles) // 2]
        self.stairs_down = [(sd[0], sd[1])]
        self.floor_type[sd[1]][sd[0]] = TILE_STAIRS_DOWN

    def _add_grass_patches(self):
        for _ in range(60):
            gx = random.randint(5, self.width - 6)
            gy = random.randint(5, self.height - 6)
            gr = random.randint(2, 5)
            for dy in range(-gr, gr + 1):
                for dx in range(-gr, gr + 1):
                    if dx * dx + dy * dy <= gr * gr:
                        nx, ny = gx + dx, gy + dy
                        if 0 < nx < self.width and 0 < ny < self.height:
                            if self.grid[ny][nx] == TILE_FLOOR:
                                self.floor_type[ny][nx] = TILE_GRASS

    def _add_water_features(self):
        for _ in range(15):
            wx = random.randint(8, self.width - 9)
            wy = random.randint(8, self.height - 9)
            wr = random.randint(2, 4)
            for dy in range(-wr, wr + 1):
                for dx in range(-wr, wr + 1):
                    if dx * dx + dy * dy <= wr * wr:
                        nx, ny = wx + dx, wy + dy
                        if 0 < nx < self.width and 0 < ny < self.height:
                            if self.grid[ny][nx] == TILE_FLOOR:
                                self.floor_type[ny][nx] = TILE_WATER

    def update_doors(self, dt):
        for door in self.doors:
            door.update(dt)

    def try_open_door(self, x, y):
        for door in self.doors:
            if door.x == int(x) and door.y == int(y):
                door.toggle()
                return True
            if abs(door.x + 0.5 - x) < 1.2 and abs(door.y + 0.5 - y) < 1.2:
                door.toggle()
                return True
        return False

    def is_wall(self, x, y):
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= self.width or iy < 0 or iy >= self.height:
            return True
        cell = self.grid[iy][ix]
        if cell == TILE_WALL:
            return True
        if cell == TILE_DOOR:
            for door in self.doors:
                if door.x == ix and door.y == iy:
                    return door.blocks()
            return True
        return False

    def is_water(self, x, y):
        ix, iy = int(x), int(y)
        if 0 <= ix < self.width and 0 <= iy < self.height:
            return self.floor_type[iy][ix] == TILE_WATER
        return False

    def get_floor_type(self, x, y):
        ix, iy = int(x), int(y)
        if 0 <= ix < self.width and 0 <= iy < self.height:
            return self.floor_type[iy][ix]
        return TILE_FLOOR

    def get_tex_id(self, x, y):
        ix, iy = int(x), int(y)
        if 0 <= ix < self.width and 0 <= iy < self.height:
            return self.tex_map[iy][ix]
        return 0

    def get_spawn(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == TILE_FLOOR:
                    return (x + 0.5, y + 0.5)
        return (self.width // 2 + 0.5, self.height // 2 + 0.5)

    def get_floor_tiles(self):
        tiles = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == TILE_FLOOR:
                    tiles.append((x, y))
        return tiles

    def minimap(self, cell_size=6):
        import pygame
        surf = pygame.Surface((self.width * cell_size, self.height * cell_size))
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == TILE_WALL:
                    tid = self.tex_map[y][x]
                    colors = [(160, 80, 40), (120, 120, 120), (150, 150, 160), (130, 85, 40), (140, 140, 135), (200, 190, 210), (130, 120, 110), (180, 160, 110)]
                    c = colors[tid % len(colors)]
                elif self.grid[y][x] == TILE_DOOR:
                    c = (140, 100, 50)
                elif self.floor_type[y][x] == TILE_WATER:
                    c = (40, 80, 180)
                elif self.floor_type[y][x] == TILE_GRASS:
                    c = (60, 140, 50)
                elif self.floor_type[y][x] == TILE_STAIRS_UP:
                    c = (180, 180, 60)
                elif self.floor_type[y][x] == TILE_STAIRS_DOWN:
                    c = (180, 120, 60)
                else:
                    c = (180, 180, 180)
                surf.fill(c, (x * cell_size, y * cell_size, cell_size, cell_size))
        return surf
