# HexForge

A first-person shooter built entirely in Python using Pygame. Features a Wolfenstein 3D-style raycasting engine, procedurally generated dungeons, procedural textures and audio, multiple weapons with upgrades, wave-based enemy AI, and a full menu/shop system. No external assets required -- everything is generated at runtime.

## Installation

```bash
pip install -r requirements.txt
```

**Dependencies:** `pygame>=2.6`, `numpy>=1.24`

## Running

From the /src/dir like so:

```bash
```bash
cd src
python main.py
```

Or like so directly from the project root directory:

```bash
python src/main.py
```

```
```
On first launch, procedural textures are generated and cached to `texture_cache/`. This takes a few seconds.

## Controls

| Action | Key |
|---|---|
| Move | W A S D |
| Look | Mouse |
| Shoot | Left Click |
| Aim Down Sights | Right Click |
| Reload | R |
| Jump | Space |
| Interact (Doors) | E |
| Weapon 1 (AK47) | 1 |
| Weapon 2 (Glock19) | 2 |
| Weapon 3 (Knife) | 3 |
| Weapon 4 (Grenade) | 4 |
| Quit / Back | Escape |

## Weapons

| Weapon | Type | Damage | Fire Rate | Mag | Reserve | Reload |
|---|---|---|---|---|---|---|
| AK47 | Auto Rifle | 30 | 0.10s | 30 | 90 | 2.4s |
| Glock19 | Semi-Auto | 25 | 0.18s | 17 | 68 | 1.8s |
| Knife | Melee | 60 | 0.50s | -- | -- | -- |
| Grenade | Throwable | 50 | 0.80s | 1 | 0 | -- |

Each weapon is drawn with procedural polygon art, features kickback, sway, muzzle flash, and shell ejection. The grenade has a parabolic arc, 1.5s fuse, wall bounce, and distance-based damage falloff.

### Upgrades

**AK47:**
| Upgrade | Cost | Effect |
|---|---|---|
| Extended Mag | $400 | 30 -> 45 round magazine |
| Damage Boost | $600 | 30 -> 40 damage |
| Rapid Fire | $500 | 0.10s -> 0.07s fire rate |

**Glock19:**
| Upgrade | Cost | Effect |
|---|---|---|
| Extended Mag | $300 | 17 -> 25 round magazine |
| Damage Boost | $400 | 25 -> 33 damage |
| Rapid Fire | $350 | 0.18s -> 0.12s fire rate |

**Grenade:**
| Upgrade | Cost | Effect |
|---|---|---|
| Extra Nades | $250 | +2 grenades |
| Blast Radius | $500 | Larger explosion area |
| More Damage | $450 | 50 -> 75 damage |

## Gameplay

### Waves
Enemies spawn in waves of 8. Each wave increases enemy HP (+40) and speed (+0.3). Killing all enemies advances the wave. Earn $100 per kill.

### Enemies
Enemies chase the player and fire back when in range. They scale in difficulty each wave. Displayed as colored humanoid shapes with HP-based targeting reticles.

### Health
10 hit points displayed as hearts. Taking damage shows a red flash. Death triggers a respawn after 2 seconds.

### Doors
Press E near doors to open/close them. Doors animate and block movement until mostly open.

### Aiming
Right-click narrows FOV from 85 to 45 degrees for precision aiming with a scope overlay.

### Jumping
Space bar launches the player upward with gravity pulling back down. Affects rendering offset for walls and floor.

## Map

A 100x100 procedurally generated dungeon with:
- Corridors carved via random walks
- Random rooms
- Doors at chokepoints between corridors
- Grass patches and water pools
- Stairs (placeholder for level progression)
- Water slows movement by 50%

A minimap in the top-left shows the layout, player position, direction, and enemy locations.

## Technical Details

| Parameter | Value |
|---|---|
| Screen | 1280x720 |
| Render Buffer | 320x180 (4x upscale) |
| Texture Size | 256x256 |
| FPS Target | 60 |
| FOV | 85 degrees |
| Map Size | 100x100 tiles |

### Rendering
- DDA raycasting for walls with per-pixel texture mapping
- Floor/ceiling casting with perspective-correct texturing
- Distance-based fog and side-based lighting
- Vignette post-processing effect
- Numpy-accelerated column rendering

### Procedural Generation
- **Textures:** 10 types (brick, stone, metal, wood, concrete, marble, cobblestone, sandstone, grass, water) generated via 5-octave fractional Brownian motion noise, cached as PNGs
- **Audio:** Gunshots, explosions, hits, UI sounds generated with numpy sine waves and noise -- no audio files
- **Maps:** Random corridor carving with rooms, doors, and environmental features

### Save System
Player progress persists to `src/save_data.json`: money, owned weapons, upgrades, and grenade count.

## Project Structure

```
HexForge/
  run.py                    # Entry point
  requirements.txt          # pygame, numpy
  README.md
  src/
    main.py                 # Launches menu
    config.py               # Constants and controls
    window.py               # Game loop, raycasting, HUD
    map.py                  # Procedural map generation
    textures.py             # Procedural texture generation
    loadout.py              # Weapon classes
    bullet.py               # Bullet physics
    target.py               # Enemy AI
    game_state.py           # Save/load, shop, upgrades
    menu.py                 # Main menu, shop, loadout screens
    sound.py                # Procedural audio
  texture_cache/            # Cached PNG textures
```
