import ctypes
import ctypes.util
import struct
import math
import os
import sys
import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders

_sdl_path = None
try:
    _sdl_path = ctypes.util.find_library("SDL2")
except Exception:
    pass

if not _sdl_path:
    try:
        import pygame as _pg
        _pg_dir = os.path.dirname(_pg.__file__)
        _candidate = os.path.join(_pg_dir, "SDL2.dll")
        if os.path.isfile(_candidate):
            _sdl_path = _candidate
        else:
            if hasattr(sys, "frozen"):
                _candidate = os.path.join(sys._MEIPASS, "SDL2.dll")
                if os.path.isfile(_candidate):
                    _sdl_path = _candidate
    except Exception:
        pass

if not _sdl_path:
    if sys.platform == "win32":
        _sdl_path = "SDL2.dll"
    else:
        _sdl_path = "libSDL2.so"

SDL = ctypes.CDLL(_sdl_path)

SDL_INIT_VIDEO = 0x00000020
SDL_INIT_EVENTS = 0x00004000
SDL_WINDOWPOS_CENTERED = 0
SDL_WINDOW_OPENGL = 0x00000002
SDL_WINDOW_RESIZABLE = 0x00000020
SDL_WINDOW_SHOWN = 0x00000004
SDL_GL_CONTEXT_MAJOR_VERSION = 0x2041
SDL_GL_CONTEXT_MINOR_VERSION = 0x2042
SDL_GL_DOUBLEBUFFER = 0x17
SDL_GL_DEPTH_SIZE = 0x1705
SDL_QUIT = 0x100
SDL_KEYDOWN = 0x300
SDL_KEYUP = 0x301
SDL_MOUSEMOTION = 0x400
SDL_MOUSEBUTTONDOWN = 0x401
SDL_MOUSEBUTTONUP = 0x402
SDL_WINDOWEVENT = 0x200
SDL_WINDOWEVENT_SIZE_CHANGED = 5
SDL_SCANCODE_W = 26
SDL_SCANCODE_S = 22
SDL_SCANCODE_A = 4
SDL_SCANCODE_D = 7
SDL_SCANCODE_R = 21
SDL_SCANCODE_E = 8
SDL_SCANCODE_SPACE = 44
SDL_SCANCODE_ESCAPE = 41
SDL_SCANCODE_1 = 30
SDL_SCANCODE_2 = 31
SDL_SCANCODE_3 = 32
SDL_SCANCODE_4 = 33
SDL_BUTTON_LEFT = 1
SDL_BUTTON_RIGHT = 3
SDL_GL_SetAttribute = SDL.SDL_GL_SetAttribute
SDL_GL_SetAttribute.restype = ctypes.c_int
SDL_GL_SetAttribute.argtypes = [ctypes.c_int, ctypes.c_int]
SDL_Init = SDL.SDL_Init
SDL_Init.restype = ctypes.c_int
SDL_Init.argtypes = [ctypes.c_uint32]
SDL_CreateWindow = SDL.SDL_CreateWindow
SDL_CreateWindow.restype = ctypes.c_void_p
SDL_CreateWindow.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
SDL_DestroyWindow = SDL.SDL_DestroyWindow
SDL_DestroyWindow.restype = None
SDL_DestroyWindow.argtypes = [ctypes.c_void_p]
SDL_GL_CreateContext = SDL.SDL_GL_CreateContext
SDL_GL_CreateContext.restype = ctypes.c_void_p
SDL_GL_CreateContext.argtypes = [ctypes.c_void_p]
SDL_GL_DeleteContext = SDL.SDL_GL_DeleteContext
SDL_GL_DeleteContext.restype = None
SDL_GL_DeleteContext.argtypes = [ctypes.c_void_p]
SDL_GL_SwapWindow = SDL.SDL_GL_SwapWindow
SDL_GL_SwapWindow.restype = None
SDL_GL_SwapWindow.argtypes = [ctypes.c_void_p]
SDL_GL_SetSwapInterval = SDL.SDL_GL_SetSwapInterval
SDL_GL_SetSwapInterval.restype = ctypes.c_int
SDL_GL_SetSwapInterval.argtypes = [ctypes.c_int]
SDL_PollEvent = SDL.SDL_PollEvent
SDL_PollEvent.restype = ctypes.c_int
SDL_PollEvent.argtypes = [ctypes.c_void_p]
SDL_GetKeyboardState = SDL.SDL_GetKeyboardState
SDL_GetKeyboardState.restype = ctypes.POINTER(ctypes.c_uint8)
SDL_GetKeyboardState.argtypes = [ctypes.POINTER(ctypes.c_int)]
SDL_GetRelativeMouseState = SDL.SDL_GetRelativeMouseState
SDL_GetRelativeMouseState.restype = ctypes.c_uint32
SDL_GetRelativeMouseState.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
SDL_WarpMouseInWindow = SDL.SDL_WarpMouseInWindow
SDL_WarpMouseInWindow.restype = None
SDL_WarpMouseInWindow.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
SDL_ShowCursor = SDL.SDL_ShowCursor
SDL_ShowCursor.restype = ctypes.c_int
SDL_ShowCursor.argtypes = [ctypes.c_int]
SDL_SetRelativeMouseMode = SDL.SDL_SetRelativeMouseMode
SDL_SetRelativeMouseMode.restype = ctypes.c_int
SDL_SetRelativeMouseMode.argtypes = [ctypes.c_int]
SDL_GetPerformanceCounter = SDL.SDL_GetPerformanceCounter
SDL_GetPerformanceCounter.restype = ctypes.c_uint64
SDL_GetPerformanceFrequency = SDL.SDL_GetPerformanceFrequency
SDL_GetPerformanceFrequency.restype = ctypes.c_uint64
SDL_GetWindowSize = SDL.SDL_GetWindowSize
SDL_GetWindowSize.restype = None
SDL_GetWindowSize.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
SDL_GetTicks = SDL.SDL_GetTicks
SDL_GetTicks.restype = ctypes.c_uint32

SDL_Event = ctypes.c_uint8 * 56


class OpenGLRenderer:
    def __init__(self, width, height, title=b"HexForge FPS"):
        SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3)
        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)
        SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24)
        self.window = SDL_CreateWindow(
            title,
            SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
            width, height,
            SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE | SDL_WINDOW_SHOWN,
        )
        if not self.window:
            raise RuntimeError("Failed to create SDL2 window")
        self.context = SDL_GL_CreateContext(self.window)
        if not self.context:
            raise RuntimeError("Failed to create OpenGL context")
        SDL_GL_SetSwapInterval(1)
        SDL_SetRelativeMouseMode(1)
        SDL_ShowCursor(0)
        self.width = width
        self.height = height
        self._init_gl()
        self._create_shaders()
        self._create_fbo()
        self._create_quad()

    def _init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glClearColor(0, 0, 0, 1)
        self._resize(self.width, self.height)

    def _resize(self, w, h):
        if h == 0:
            h = 1
        self.width = w
        self.height = h
        glViewport(0, 0, w, h)

    def handle_event(self, event):
        if event.type == SDL_WINDOWEVENT and event.window.event == SDL_WINDOWEVENT_SIZE_CHANGED:
            self._resize(event.window.data1, event.window.data2)
            return True
        return False

    def _create_shaders(self):
        vs_src = b"""
#version 330 core
layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aUV;
out vec2 vUV;
void main() {
    vUV = aUV;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""
        fs_src = b"""
#version 330 core
in vec2 vUV;
out vec4 fragColor;

uniform vec2 uScreenSize;
uniform vec2 uPlayerPos;
uniform float uAngle;
uniform float uPitch;
uniform float uFOV;
uniform float uPlayerZ;
uniform sampler2DArray uMapTex;
uniform sampler2DArray uWallTex;
uniform sampler2D uFloorTex;
uniform sampler2D uCeilTex;
uniform sampler2D uGrassTex;
uniform sampler2D uWaterTex;
uniform int uMapW;
uniform int uMapH;
uniform int uNumWalls;
uniform float uTime;
uniform float uDamageFlash;

#define PI 3.14159265359
#define MAX_DIST 64.0
#define TEX_SIZE 256.0

vec3 getWallColor(int texId, float wallX, float dist) {
    float tx = wallX;
    float ty = 0.0;
    float step = 1.0 / 256.0;
    vec3 col = vec3(0.0);
    float bestDist = MAX_DIST;
    for (int i = 0; i < 256; i++) {
        ty = (float(i) + 0.5) / 256.0;
        col = texture(uWallTex, vec3(tx, ty, float(texId))).rgb;
    }
    ty = 0.5;
    col = texture(uWallTex, vec3(tx, ty, float(texId))).rgb;
    float fog = min(1.0, dist * 0.035);
    col = mix(col, vec3(0.118, 0.110, 0.137), fog);
    return col;
}

void main() {
    vec2 uv = vUV;
    vec2 screenPos = uv * uScreenSize;
    float halfH = uScreenSize.y * 0.5;
    float halfW = uScreenSize.x * 0.5;

    vec2 rayDir;
    rayDir.x = cos(uAngle) + cos(uAngle + PI * 0.5) * (uv.x - 0.5) * tan(radians(uFOV) * 0.5) * (uScreenSize.x / uScreenSize.y);
    rayDir.y = sin(uAngle) + sin(uAngle + PI * 0.5) * (uv.x - 0.5) * tan(radians(uFOV) * 0.5) * (uScreenSize.x / uScreenSize.y);
    float fdx = rayDir.x - cos(uAngle);
    float fdy = rayDir.y - sin(uAngle);
    rayDir = normalize(vec2(fdx, fdy));

    float rayAngle = atan(rayDir.y, rayDir.x);
    float angleDiff = rayAngle - uAngle;
    while (angleDiff > PI) angleDiff -= 2.0 * PI;
    while (angleDiff < -PI) angleDiff += 2.0 * PI;

    vec2 mapPos = floor(uPlayerPos);
    vec2 deltaDist = abs(1.0 / rayDir);
    vec2 step;
    vec2 sideDist;

    if (rayDir.x < 0.0) {
        step.x = -1.0;
        sideDist.x = (uPlayerPos.x - mapPos.x) * deltaDist.x;
    } else {
        step.x = 1.0;
        sideDist.x = (mapPos.x + 1.0 - uPlayerPos.x) * deltaDist.x;
    }
    if (rayDir.y < 0.0) {
        step.y = -1.0;
        sideDist.y = (uPlayerPos.y - mapPos.y) * deltaDist.y;
    } else {
        step.y = 1.0;
        sideDist.y = (mapPos.y + 1.0 - uPlayerPos.y) * deltaDist.y;
    }

    float perpDist = 0.0;
    int side = 0;
    bool hit = false;
    int texId = 0;
    vec2 hitPos = uPlayerPos;

    for (int i = 0; i < 128; i++) {
        if (sideDist.x < sideDist.y) {
            sideDist.x += deltaDist.x;
            mapPos.x += step.x;
            side = 0;
        } else {
            sideDist.y += deltaDist.y;
            mapPos.y += step.y;
            side = 1;
        }
        if (mapPos.x < 0.0 || mapPos.x >= float(uMapW) || mapPos.y < 0.0 || mapPos.y >= float(uMapH)) break;

        int ix = int(mapPos.x);
        int iy = int(mapPos.y);
        if (ix >= 0 && ix < uMapW && iy >= 0 && iy < uMapH) {
            float tileVal = texture(uMapTex, vec3(float(ix) / float(uMapW), float(iy) / float(uMapH), 0.0)).r;
            int tileType = int(tileVal * 255.0 + 0.5);
            if (tileType == 1) {
                hit = true;
                if (side == 0) {
                    perpDist = (mapPos.x - uPlayerPos.x + (1.0 - step.x) * 0.5) / rayDir.x;
                } else {
                    perpDist = (mapPos.y - uPlayerPos.y + (1.0 - step.y) * 0.5) / rayDir.y;
                }
                hitPos = uPlayerPos + rayDir * perpDist;
                float wallX;
                if (side == 0) wallX = uPlayerPos.y + perpDist * rayDir.y;
                else wallX = uPlayerPos.x + perpDist * rayDir.x;
                wallX -= floor(wallX);

                float texVal = texture(uMapTex, vec3(float(ix) / float(uMapW), float(iy) / float(uMapH), 1.0)).r;
                texId = int(texVal * 255.0 + 0.5);
                float wallH = uScreenSize.y / perpDist;
                float screenY = halfH + uPitch - wallH * 0.5 + uPlayerZ * 30.0 / max(perpDist, 0.5);
                float wallBot = screenY + wallH;

                if (uv.y * uScreenSize.y >= screenY && uv.y * uScreenSize.y <= wallBot) {
                    float texY = (uv.y * uScreenSize.y - screenY) / wallH;
                    vec3 wallCol = texture(uWallTex, vec3(wallX, texY, float(texId))).rgb;
                    float shade = (side == 1) ? 0.6 : 1.0;
                    float distFactor = max(0.1, 1.0 - perpDist * 0.03);
                    float fog = min(1.0, perpDist * 0.035);
                    wallCol *= shade * distFactor;
                    wallCol = mix(wallCol, vec3(0.118, 0.110, 0.137), fog);
                    fragColor = vec4(wallCol, 1.0);
                    float vig = 1.0 - length((uv - 0.5) * 1.4) * 0.35;
                    vig = max(vig, 0.4);
                    fragColor.rgb *= vig;
                    fragColor.rgb = fragColor.rgb / (fragColor.rgb + vec3(1.0)) * 1.2;
                    fragColor.rgb += vec3(uDamageFlash * 0.7, 0.0, 0.0);
                    return;
                }
            }
        }
    }

    float yNorm = uv.y;
    float p = yNorm - 0.5;
    float absP = abs(p);
    if (absP < 0.001) { fragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }

    float posZ = 0.7 + uPlayerZ + uPitch * (0.5 - absP);
    float rowDist = posZ / absP / tan(radians(uFOV * 0.5));

    vec2 floorDir;
    floorDir.x = cos(uAngle + PI * 0.5) * (uv.x - 0.5) * tan(radians(uFOV) * 0.5) * (uScreenSize.x / uScreenSize.y);
    floorDir.y = sin(uAngle + PI * 0.5) * (uv.x - 0.5) * tan(radians(uFOV) * 0.5) * (uScreenSize.x / uScreenSize.y);
    vec2 baseDir = vec2(cos(uAngle), sin(uAngle));
    floorDir = baseDir + floorDir;
    floorDir = normalize(floorDir) * length(vec2((uv.x - 0.5) * tan(radians(uFOV) * 0.5) * (uScreenSize.x / uScreenSize.y), 1.0));

    vec2 worldPos = uPlayerPos + floorDir * rowDist;
    vec3 floorCol;
    bool isFloor = (yNorm > 0.5);

    if (isFloor) {
        int tx = clamp(int(worldPos.x), 0, uMapW - 1);
        int ty = clamp(int(worldPos.y), 0, uMapH - 1);
        float fVal = texture(uMapTex, vec3(float(tx) / float(uMapW), float(ty) / float(uMapH), 2.0)).r;
        int floorType = int(fVal * 255.0 + 0.5);
        float texS = 1.5;
        vec2 tc = fract(worldPos * texS);
        if (floorType == 3) {
            floorCol = texture(uGrassTex, tc).rgb;
        } else if (floorType == 2) {
            float wave = sin(worldPos.x * 4.0 + uTime * 2.0) * 0.03 + sin(worldPos.y * 3.0 + uTime * 1.5) * 0.02;
            floorCol = texture(uWaterTex, tc + wave).rgb;
        } else {
            floorCol = texture(uFloorTex, tc).rgb;
        }
    } else {
        vec2 tc = fract(worldPos * 1.2);
        floorCol = texture(uCeilTex, tc).rgb;
    }

    float fog = min(1.0, rowDist * 0.045);
    floorCol = mix(floorCol, vec3(0.098, 0.086, 0.110), fog);
    float vig = 1.0 - length((uv - 0.5) * 1.4) * 0.35;
    vig = max(vig, 0.4);
    floorCol *= vig;
    floorCol = floorCol / (floorCol + vec3(1.0)) * 1.2;
    floorCol += vec3(uDamageFlash * 0.7, 0.0, 0.0);
    fragColor = vec4(floorCol, 1.0);
}
"""
        vs = shaders.compileShader(vs_src, GL_VERTEX_SHADER)
        fs = shaders.compileShader(fs_src, GL_FRAGMENT_SHADER)
        self.ray_program = shaders.compileProgram(vs, fs)
        self.ray_locs = {}
        for name in ["uScreenSize", "uPlayerPos", "uAngle", "uPitch", "uFOV",
                       "uPlayerZ", "uMapTex", "uWallTex", "uFloorTex", "uCeilTex",
                       "uGrassTex", "uWaterTex", "uMapW", "uMapH", "uNumWalls",
                       "uTime", "uDamageFlash"]:
            self.ray_locs[name] = glGetUniformLocation(self.ray_program, name)

        hud_vs = b"""
#version 330 core
layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aUV;
out vec2 vUV;
void main() {
    vUV = aUV;
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""
        hud_fs = b"""
#version 330 core
in vec2 vUV;
out vec4 fragColor;
uniform sampler2D uTex;
void main() {
    vec4 c = texture(uTex, vUV);
    if (c.a < 0.01) discard;
    fragColor = c;
}
"""
        hvs = shaders.compileShader(hud_vs, GL_VERTEX_SHADER)
        hfs = shaders.compileShader(hud_fs, GL_FRAGMENT_SHADER)
        self.hud_program = shaders.compileProgram(hvs, hfs)
        self.hud_locs = {}
        for name in ["uTex"]:
            self.hud_locs[name] = glGetUniformLocation(self.hud_program, name)

        plain_vs = b"""
#version 330 core
layout(location = 0) in vec2 aPos;
void main() {
    gl_Position = vec4(aPos, 0.0, 1.0);
}
"""
        plain_fs = b"""
#version 330 core
out vec4 fragColor;
uniform vec4 uColor;
void main() {
    fragColor = uColor;
}
"""
        pvs = shaders.compileShader(plain_vs, GL_VERTEX_SHADER)
        pfs = shaders.compileShader(plain_fs, GL_FRAGMENT_SHADER)
        self.plain_program = shaders.compileProgram(pvs, pfs)
        self.plain_locs = {}
        for name in ["uColor"]:
            self.plain_locs[name] = glGetUniformLocation(self.plain_program, name)

    def _create_fbo(self):
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        self.fbo_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.fbo_tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.fbo_tex, 0)
        rbo = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, self.width, self.height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rbo)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _create_quad(self):
        vertices = np.array([
            -1, -1, 0, 0,
             1, -1, 1, 0,
             1,  1, 1, 1,
            -1, -1, 0, 0,
             1,  1, 1, 1,
            -1,  1, 0, 1,
        ], dtype=np.float32)
        self.quad_vao = glGenVertexArrays(1)
        self.quad_vbo = glGenBuffers(1)
        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))
        glBindVertexArray(0)

    def create_map_texture(self, grid, tex_map, floor_type, w, h):
        data = np.zeros((w, h, 3), dtype=np.uint8)
        for y in range(h):
            for x in range(w):
                data[y, x, 0] = grid[y][x]
                data[y, x, 1] = tex_map[y][x]
                data[y, x, 2] = floor_type[y][x]
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, tex)
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGB, w, h, 1, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        return tex

    def create_wall_texture_array(self, tex_data_list):
        n = len(tex_data_list)
        h, w, c = tex_data_list[0].shape
        data = np.stack(tex_data_list, axis=0)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, tex)
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_RGB, w, h, n, 0, GL_RGB, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_REPEAT)
        return tex

    def create_texture_2d(self, data):
        h, w = data.shape[:2]
        c = data.shape[2] if data.ndim == 3 else 1
        if c == 3:
            fmt = GL_RGB
        else:
            fmt = GL_RGBA
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, fmt, w, h, 0, fmt, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        return tex

    def create_texture_from_surface(self, surface):
        w, h = surface.get_size()
        data = pygame.image.tostring(surface, "RGBA", True)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        return tex, w, h

    def begin_frame(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def render_scene(self, player_x, player_y, angle, pitch, fov, player_z,
                     map_tex, wall_tex, floor_tex, ceil_tex, grass_tex, water_tex,
                     map_w, map_h, num_walls, time_val, damage_flash):
        glDisable(GL_BLEND)
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)
        glUseProgram(self.ray_program)
        glUniform2f(self.ray_locs["uScreenSize"], self.width, self.height)
        glUniform2f(self.ray_locs["uPlayerPos"], player_x, player_y)
        glUniform1f(self.ray_locs["uAngle"], angle)
        glUniform1f(self.ray_locs["uPitch"], pitch)
        glUniform1f(self.ray_locs["uFOV"], fov)
        glUniform1f(self.ray_locs["uPlayerZ"], player_z)
        glUniform1i(self.ray_locs["uMapTex"], 0)
        glUniform1i(self.ray_locs["uWallTex"], 1)
        glUniform1i(self.ray_locs["uFloorTex"], 2)
        glUniform1i(self.ray_locs["uCeilTex"], 3)
        glUniform1i(self.ray_locs["uGrassTex"], 4)
        glUniform1i(self.ray_locs["uWaterTex"], 5)
        glUniform1i(self.ray_locs["uMapW"], map_w)
        glUniform1i(self.ray_locs["uMapH"], map_h)
        glUniform1i(self.ray_locs["uNumWalls"], num_walls)
        glUniform1f(self.ray_locs["uTime"], time_val)
        glUniform1f(self.ray_locs["uDamageFlash"], damage_flash)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D_ARRAY, map_tex)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D_ARRAY, wall_tex)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, floor_tex)
        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, ceil_tex)
        glActiveTexture(GL_TEXTURE4)
        glBindTexture(GL_TEXTURE_2D, grass_tex)
        glActiveTexture(GL_TEXTURE5)
        glBindTexture(GL_TEXTURE_2D, water_tex)

        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

    def draw_quad(self, x, y, w, h, color):
        x1 = (x / self.width) * 2 - 1
        y1 = 1 - (y / self.height) * 2
        x2 = ((x + w) / self.width) * 2 - 1
        y2 = 1 - ((y + h) / self.height) * 2
        verts = np.array([
            x1, y1, x2, y1, x2, y2,
            x1, y1, x2, y2, x1, y2,
        ], dtype=np.float32)
        glDisable(GL_DEPTH_TEST)
        glUseProgram(self.plain_program)
        glUniform4f(self.plain_locs["uColor"], *color)
        glBindVertexArray(self.quad_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, verts.nbytes, verts, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        glEnable(GL_DEPTH_TEST)

    def draw_hud_texture(self, tex, tex_w, tex_h, screen_w, screen_h):
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(self.hud_program)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex)
        glUniform1i(self.hud_locs["uTex"], 0)
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        glEnable(GL_DEPTH_TEST)

    def end_frame(self):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)
        glUseProgram(self.hud_program)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.fbo_tex)
        glUniform1i(self.hud_locs["uTex"], 0)
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        glEnable(GL_DEPTH_TEST)
        SDL_GL_SwapWindow(self.window)

    def end_frame_with_hud(self, hud_rgba_bytes, hud_w, hud_h):
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glUseProgram(self.hud_program)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.fbo_tex)
        glUniform1i(self.hud_locs["uTex"], 0)
        glBindVertexArray(self.quad_vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        hud_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, hud_tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, hud_w, hud_h, 0, GL_RGBA, GL_UNSIGNED_BYTE, hud_rgba_bytes)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D, hud_tex)
        glUniform1i(self.hud_locs["uTex"], 0)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glDeleteTextures(1, [hud_tex])

        glBindVertexArray(0)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        SDL_GL_SwapWindow(self.window)

    def get_keys(self):
        num = ctypes.c_int(0)
        state = SDL_GetKeyboardState(ctypes.byref(num))
        keys = {}
        for i in range(min(num.value, 512)):
            if state[i]:
                keys[i] = True
        return keys

    def get_mouse_rel(self):
        x = ctypes.c_int(0)
        y = ctypes.c_int(0)
        buttons = SDL_GetRelativeMouseState(ctypes.byref(x), ctypes.byref(y))
        left = bool(buttons & (1 << 0))
        right = bool(buttons & (1 << 2))
        return x.value, y.value, left, right

    def poll_event(self):
        event = SDL_Event()
        if SDL_PollEvent(ctypes.byref(event)):
            return event
        return None

    def quit(self):
        SDL_DestroyWindow(self.window)


import pygame

SDLK_SCANCODE_MAP = {
    SDL_SCANCODE_W: 119, SDL_SCANCODE_S: 115,
    SDL_SCANCODE_A: 97, SDL_SCANCODE_D: 100,
    SDL_SCANCODE_R: 114, SDL_SCANCODE_E: 101,
    SDL_SCANCODE_SPACE: 32, SDL_SCANCODE_ESCAPE: 27,
    SDL_SCANCODE_1: 49, SDL_SCANCODE_2: 50,
    SDL_SCANCODE_3: 51, SDL_SCANCODE_4: 52,
}


def scancode_to_pygame(scancode):
    return SDLK_SCANCODE_MAP.get(scancode, 0)
