# HexForge

A Wolfenstein 3D-style first-person shooter written in Python with **pygame** and **numpy**. It runs a classic DDA raycasting engine, procedurally generates its textures, audio, and dungeon layouts at runtime, and wraps it all in a shop / loadout / wave-based progression loop. No external assets are required — everything is created on first launch.

> **Rendering roadmap:** we are currently shipping with a classic **Wolfenstein 3D** raycaster, and we are planning to migrate to a modern, **Fortnite-like 3D "fashion" style renderer** (cell-shaded, vibrant, character-customization driven visuals) down the line.

## Features

- **Raycasting renderer** — per-pixel textured walls, perspective-correct floor/ceiling casting, distance fog, side-based shading, and a vignette effect (numpy-accelerated).
- **Procedural textures** — 10 surface types (brick, stone, metal, wood, concrete, marble, cobblestone, sandstone, grass, water) generated with 5-octave fractional Brownian motion noise and cached to `texture_cache/`.
- **Procedural audio** — gunshots, explosions, hits, and UI clicks synthesized with numpy — no sound files.
- **Procedural dungeons** — a 100x100 map with carved corridors, random rooms, doors, grass patches, water pools, and stairs.
- **Wave combat** — 8 enemies per wave that chase and shoot; HP and speed scale every wave. Each kill pays **$100**.
- **Shop & loadout** — buy weapons and upgrades with money earned in-game; progress persists to disk.
- **Weapon handling** — kickback, sway, muzzle flash, shell ejection, reload bars, and a parabolic, bouncy grenade with blast falloff.

## Requirements

- Python 3.10+
- `pygame>=2.6`
- `numpy>=1.24`

## Installation

```bash
pip install -r requirements.txt
```

## Running

From the project root:

```bash
python run.py
```

or directly:

```bash
python src/main.py
```

On first launch, procedural textures are generated and cached to `texture_cache/`. This takes a few seconds.

### Standalone executable

A prebuilt, windowed executable is produced in `dist/HexForge.exe` — double-click it to play. Saves and the texture cache are written next to the executable.

## Controls

| Action | Key |
|---|---|
| Move | W A S D |
| Look | Mouse |
| Shoot | Left Click |
| Aim Down Sights (scope + zoom) | Right Click |
| Reload | R |
| Jump | Space |
| Interact (doors) | E |
| Weapon 1 (AK47) | 1 |
| Weapon 2 (Glock19) | 2 |
| Weapon 3 (Knife) | 3 |
| Weapon 4 (Grenade) | 4 |
| Quit / Back to menu | Escape |

## Weapons

| Weapon | Type | Damage | Fire Rate | Mag | Reserve | Reload |
|---|---|---|---|---|---|---|
| AK47 | Auto Rifle | 30 | 0.10s | 30 | 90 | 2.4s |
| Glock19 | Semi-Auto | 25 | 0.18s | 17 | 68 | 1.8s |
| Knife | Melee | 60 | 0.50s | — | — | — |
| Grenade | Throwable | 50 | 0.80s | 1 | — | 1.5s fuse |

The AK47 uses the `texture_cache/Gun.png` sprite, while the other weapons are drawn with procedural polygon art; all feature kickback, sway, muzzle flash, and shell ejection. Grenades arc through the air, bounce off walls, and deal distance-based splash damage.

### Shop prices

| Item | Cost |
|---|---|
| AK47 (starter) | $0 |
| Glock19 | $500 |
| Knife | $300 |
| Grenade | $200 |

### Upgrades

**AK47**

| Upgrade | Cost | Effect |
|---|---|---|
| Extended Mag | $400 | 30 -> 45 rounds |
| Damage Boost | $600 | 30 -> 40 damage |
| Rapid Fire | $500 | 0.10s -> 0.07s fire rate |

**Glock19**

| Upgrade | Cost | Effect |
|---|---|---|
| Extended Mag | $300 | 17 -> 25 rounds |
| Damage Boost | $400 | 25 -> 33 damage |
| Rapid Fire | $350 | 0.18s -> 0.12s fire rate |

**Grenade**

| Upgrade | Cost | Effect |
|---|---|---|
| Extra Nades | $250 | +2 grenades |
| Blast Radius | $500 | Larger explosion radius |
| More Damage | $450 | 50 -> 75 explosion damage |

## Gameplay

- **Waves** — enemies spawn in waves of 8. Each wave adds +40 HP and +0.3 speed to enemies. Clearing a wave advances you; dying resets the wave.
- **Enemies** — humanoid shapes that chase the player and fire back when in range. Their HP reticle colors shift green -> yellow -> red as they weaken.
- **Health** — 10 hit points shown as hearts. Taking damage triggers a red flash; at 0 HP you respawn after 2 seconds.
- **Doors** — press E near a door to open or close it; doors animate and block movement until mostly open.
- **Aiming** — right-click narrows the FOV from 85 to 45 degrees and overlays a scope.
- **Jumping** — Space launches the player with gravity, affecting the rendered view height.
- **Water** — slows movement by 50%.

## Map

A 100x100 procedurally generated dungeon featuring:
- Corridors carved via random walks
- Random rooms
- Doors at corridor chokepoints
- Grass patches and water pools
- Stairs (placeholder for level progression)

A minimap in the top-left shows the layout, your position/direction, and color-coded enemy locations.

## Save System

Progress persists to `src/save_data.json` when run from source (or next to the executable in a frozen build): money, owned weapons, grenade count, and purchased upgrades.

## Roadmap

A growing list of planned content and features. Everything here is scheduled for upcoming releases — nothing is guaranteed to ship exactly as described.

### Planned weapons

| Weapon | Type | Damage | Fire Rate | Mag | Notes |
|---|---|---|---|---|---|
| Shotgun | Pump-Action | 80 (8 pellets x 10) | 1.0s | 6 | Wide spread, short range; devastating up close |
| SMG | Auto SMG | 18 | 0.06s | 32 | High fire rate, low damage per shot, high recoil |
| Sniper Rifle | Bolt-Action | 150 | 1.4s | 5 | High zoom scope, heavy recoil, penetrates enemies |
| Rocket Launcher | Explosive | 120 | 1.2s | 1 | Slow projectile with splash damage and self-damage |
| Flamethrower | Fire | 15 | 0.05s | 60 | Continuous stream, sets enemies ablaze (DoT) |
| Revolver | Six-Shooter | 55 | 0.35s | 6 | Powerful, precise, quick fan-fire while jumping |
| Katana | Melee | 90 | 0.45s | — | Fast sweep attack that can deflect enemy shots |
| Dual Pistols | Dual-Wield | 20 each | 0.12s | 30 | Two triggers alternate fire; inaccurate when moving |
| Crossbow | Ranged | 70 | 0.9s | 1 | Silent, retrievable bolts; can pin enemies to walls |
| Laser Rifle | Energy | 40 | 0.20s | 24 | Hitscan beam, no bullet drop, heat-overheat mechanic |

### Planned maps

| Map | Theme | Description |
|---|---|---|
| The Foundry | Industrial | Molten lava chasms, blast furnaces, and catwalk platforms over fire pools |
| Cold Storage | Frozen Vault | Icy corridors, slippery floors, and frozen water hazards |
| The Catacombs | Ancient Ruins | Crumbling stone tombs, trap floors, and a sealed crypt boss arena |
| Overgrown Labs | Abandoned Research | Glass-walled labs, plant-choked rooms, and a malfunctioning reactor core |
| Hover City | Futuristic Skyline | Floating platforms over an endless void; falling = instant respawn |
| Death Match Arena | Competitive | Symmetrical map built for PvP and time-trial modes |
| The Bunker | Military | Multi-level bunker with pillboxes, air vents, and a central elevator shaft |
| Temple of the Sun | Desert | Sun-drenched sandstone temple with pressure-plate traps and a treasure vault |

### Planned ores, pickups & interactables

- **New ores** — gold, crystal, plasma, and rune deposits scattered across maps that can be mined for bonus cash and crafting materials.
- **Pickups** — armor vests, medkits, ammo crates, speed boots, shield cells, and temporary "rage" power-ups.
- **Vendors & crafting stations** — repair benches, ammo printers, and upgrade forges that let you spend ores mid-run.
- **Explosive barrels** — shootable environmental hazards that chain-react.

### Planned gameplay & systems

- **Modern 3D "fashion" renderer** — migrate from the Wolfenstein-style raycaster to a Fortnite-like cell-shaded, vibrant, character-customization-driven renderer (see the rendering note above).
- **Boss battles** — multi-phase arena bosses at the end of each map.
- **Enemy variety** — rushers, spitters, shielded soldiers, turrets, and flying drones.
- **Procedural map seeds** — shareable seed strings so players can compare dungeons.
- **Difficulty settings** — Casual, Standard, and Nightmare modes.
- **New game modes** — endless survival, arena challenges, and speedrun timers.
- **Leaderboards & stats** — persistent kill/death tracking and global leaderboard support.
- **Multiplayer (long-term)** — co-op and PvP deathmatch via the `server/` scaffolding.
- **Audio enhancements** — positional audio, reverb in large rooms, and dynamic music that escalates during combat.
- **Controller support** — gamepad bindings and aim assist.

## Technical Details

| Parameter | Value |
|---|---|
| Screen | 1280x720 |
| Render buffer | 320x180 (4x upscale) |
| Texture size | 256x256 |
| FPS target | 60 |
| FOV | 85 degrees (45 when aiming) |
| Map size | 100x100 tiles |

### Rendering

- DDA raycasting with per-pixel texture mapping
- Floor/ceiling casting with perspective-correct texturing
- Distance-based fog and side-based lighting
- Vignette post-processing
- numpy-accelerated column and floor/ceiling rendering

### Procedural generation

- **Textures:** 10 types generated with 5-octave fBm noise, cached as PNGs
- **Audio:** gunshots, explosions, hits, and UI sounds synthesized with numpy
- **Maps:** random corridor carving with rooms, doors, and environmental features

## Project Structure

```
HexForge/
  run.py                    # Root entry point (from src import main)
  HexForge.spec             # PyInstaller build config
  requirements.txt          # pygame, numpy
  src/
    main.py                 # Launches the menu
    menu.py                 # Main menu, shop, loadout screens
    window.py               # Game loop, raycasting, HUD, particles
    map.py                  # Procedural dungeon generation
    textures.py             # Procedural texture generation + cache
    loadout.py              # Weapon classes and viewmodels
    bullet.py               # Bullet physics and shell/muzzle effects
    target.py               # Enemy AI and rendering
    game_state.py           # Save/load, shop economy, upgrades
    sound.py                # Procedural audio synthesis
    config.py               # Constants and control bindings
  texture_cache/            # Cached procedural PNG textures
  frontend/browser-site/    # React + TypeScript + Vite site scaffold
  backend/                  # Empty backend scaffolding
  server/                   # Empty server / database scaffolding
  tests/                    # Empty test scaffolding
```

## Building the executable

```bash
pip install pyinstaller
pyinstaller HexForge.spec --noconfirm
```

The build outputs `dist/HexForge.exe` (windowed, single-file). When frozen, `save_data.json` and `texture_cache/` are created alongside the executable so progress and texture caches persist.
