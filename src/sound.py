import pygame as pg
import numpy as np

_initialized = False
_sounds = {}


def init():
    global _initialized
    if _initialized:
        return
    try:
        pg.mixer.init(frequency=22050, size=-16, channels=1)
        _sounds["gunshot"] = _make_sound(0.12, 800, 0.6)
        _sounds["pistol"] = _make_sound(0.08, 600, 0.5)
        _sounds["knife"] = _make_sound(0.06, 200, 0.35)
        _sounds["grenade"] = _make_sound(0.4, 300, 0.8)
        _sounds["hit"] = _make_sound(0.08, 400, 0.4)
        _sounds["explosion"] = _make_explosion()
        _sounds["click"] = _make_sound(0.03, 1200, 0.2)
        _initialized = True
    except Exception:
        _initialized = False


def _make_sound(duration, noise_scale, volume):
    sample_rate = 22050
    n = int(sample_rate * duration)
    if n < 10:
        return None

    noise = np.random.randn(n).astype(np.float32)
    env = np.exp(-np.arange(n) / (sample_rate * 0.015))
    wave = noise * env * 0.4

    tone = np.sin(2 * np.pi * (noise_scale * 0.2) * np.arange(n) / sample_rate)
    wave += tone * env * 0.15

    wave *= volume
    wave = np.clip(wave, -1, 1)
    samples = np.int16(wave * 32767 * 0.6)

    try:
        return pg.sndarray.make_sound(samples)
    except Exception:
        return None


def _make_explosion():
    sample_rate = 22050
    duration = 0.5
    n = int(sample_rate * duration)
    if n < 10:
        return None

    noise = np.random.randn(n).astype(np.float32)
    env = np.exp(-np.arange(n) / (sample_rate * 0.06))

    rumble = np.sin(2 * np.pi * 60 * np.arange(n) / sample_rate) * 0.5
    crackle = np.random.randn(n).astype(np.float32) * 0.3

    wave = (noise * 0.3 + rumble + crackle * env) * env * 0.7
    wave = np.clip(wave, -1, 1)
    samples = np.int16(wave * 32767 * 0.7)

    try:
        return pg.sndarray.make_sound(samples)
    except Exception:
        return None


def play_gunshot():
    s = _sounds.get("gunshot")
    if s:
        s.play()


def play_pistol():
    s = _sounds.get("pistol")
    if s:
        s.play()


def play_knife():
    s = _sounds.get("knife")
    if s:
        s.play()


def play_grenade_throw():
    s = _sounds.get("grenade")
    if s:
        s.play()


def play_explosion():
    s = _sounds.get("explosion")
    if s:
        s.play()


def play_hit():
    s = _sounds.get("hit")
    if s:
        s.play()


def play_click():
    s = _sounds.get("click")
    if s:
        s.play()
