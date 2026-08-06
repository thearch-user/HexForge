# HexForge

A Wolfenstein 3D-style first-person shooter written in Python with **pygame** and **numpy**. It runs a classic DDA raycasting engine, procedurally generates its textures, audio, and dungeon layouts at runtime, and wraps it all in a shop / loadout / wave-based progression loop. No external assets are required — everything is created on first launch.

> **The Future of HexForge:** we are currently shipping with a classic **Wolfenstein 3D raycaster**, but we are planning to migrate to a modern, **Fortnite-style renderer** — a vibrant, cell-shaded, character-customization-driven 3D look with built-in building, emotes, and cosmetic loadouts. See [The Future of HexForge](#the-future-of-hexforge) below.

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

## The Future of HexForge

HexForge started life as a love letter to classic raycasters, and that's where it will stay today. But the renderer, the world, and the way you look in it are all being rethought. Here is what's coming.

### Rendering: from Wolfenstein 3D to a Fortnite-style engine

The biggest change on the horizon is a full migration from the current **Wolfenstein 3D raycaster** to a modern, **Fortnite-inspired renderer**:

- **Cell-shaded, vibrant visuals** — bold outlines, saturated materials, and clean lighting instead of flat textured columns.
- **Third-person, buildable world** — the classic wall-crawler view gives way to a smooth, camera-driven 3D perspective with on-the-fly building mechanics.
- **Character customization** — skins, outfits, emotes, gliders, and cosmetics that make *you* the center of the storm.
- **Physics-driven map events** — dynamic storm circles, destructible cover, and ziplines across the map.
- **The road there** — we will ship the Fortnite-style renderer incrementally: first a modernized lighting and material pass on the current engine, then a proper 3D geometry pipeline, and finally the full cosmetic and building systems.

### Future maps

Our hand-picked slate of new battlefields (each gets its own theme, hazards, and secrets):

| Map | Theme | Description |
|---|---|---|
| Neon Undergrid | Cyberpunk Metro | Rain-slick subway tunnels, flickering holograms, and an abandoned train that ferries players between sectors |
| Emberfall Peaks | Volcanic Alpine | A snow-capped volcano riddled with lava vents; erupting geysers launch players sky-high |
| Ghost Marina | Abandoned Coast | A foggy fishing town where the tide rises and falls, flooding the market street every few minutes |
| Crystal Caverns | Bioluminescent | Glowing crystal shards that shatter for cash, hidden echo-pools that mask footsteps |
| Sky Harbor | Floating Airport | Suspended terminals over open air, connected by gusts of wind and glass bridges that can be shot out |
| The Vault | Bank Heist | A gold-filled mega-vault with laser-grid corridors, a drillable wall, and an armory worth raiding |
| Solar Fields | Greenhouse Dome | A glass-domed farm colony; sprinklers slow you down and sunlight beams burn anyone in their path |
| Blackout Prison | Maximum Security | A riot-torn supermax with electrified fences, guard towers, and a lockdown mode that seals the exits |
| Nuclear Fallout | Post-Apocalyptic Wasteland | A bombed-out city under permanent ashfall; radiation zones tick your HP, crumbling buildings, and a sealed bunker stocked with the best loot |

### Future weapons

A brand-new arsenal we have in the works (beyond the current AK47 / Glock19 / Knife / Grenade lineup). It's split into two lanes: **grounded, realistic firearms** and **speculative sci-fi hardware**.

### Realistic weapons

Guns you'd actually find in a gun safe, with real-world handling and ballistics:

| Weapon | Type | Damage | Fire Rate | Mag | Notes |
|---|---|---|---|---|---|
| M4A1 Carbine | Assault Rifle | 28 | 0.09s | 30 | Full-auto with tight burst control; the modern upgrade to the AK47 |
| Mossberg 590 Shotgun | Pump-Action | 85 (9 pellets x ~9) | 0.9s | 8 | Pump the slide after every shot; devastating at point blank |
| UMP45 SMG | Submachine Gun | 22 | 0.07s | 25 | Low recoil, steady spray; reliable room-clearer |
| Desert Eagle | Heavy Pistol | 60 | 0.3s | 7 | .50 AE kick; punches through light cover |
| Barrett M82 | Anti-Material Rifle | 160 | 1.5s | 10 | .50 BMG that drops enemies in one; huge muzzle blast |
| M16A4 | Burst Rifle | 32 | 0.13s (3-round burst) | 30 | Three-round burst, high first-shot accuracy |
| Kriss Vector | SMG | 25 | 0.05s | 30 | Hyper-cyclic rate; recoil cancels via its delayed blowback design |
| M79 Thumper | Grenade Launcher | 110 (splash) | 1.2s | 1 | Lobbed 40mm rounds with arcing trajectories |
| MK2 Smoke Grenade | Utility | — | 0.8s | 1 | Covers your movement and marks positions for airstrikes |

### Sci-fi weapons

Speculative hardware for the far-future side of the roadmap:

| Weapon | Type | Damage | Fire Rate | Notes |
|---|---|---|---|---|
| Railgun | Energy | 200 | 1.6s | Charge-up shot that pierces enemies **and** walls; overcharge for extra damage |
| Minigun | Heavy Auto | 20 | 0.05s | Spools up before firing; wildly inaccurate until fully spun |
| Plasma Cutter | Energy | 45 | 0.35s | Fires a bouncing energy disc that ricochets off walls up to 5 times |
| Cryo Blaster | Freeze | 10 | 0.15s | Chills targets on hit; fully frozen enemies shatter into shards |
| Gravity Hammer | Melee | 120 | 0.7s | Heavy swing that sends enemies flying and creates a knockback shockwave |
| Arc Thrower | Electric | 35 | 0.4s | Chain lightning that jumps between nearby enemies |
| Sawblade Launcher | Utility | 70 | 1.0s | Spinning blades that embed in walls and can be picked back up |
| The Longshot | Sniper | 180 | 1.8s | Massive zoom, hitscan, and a lens-flare that gives your position away |

### Other long-term plans

- **Boss battles** — multi-phase arena bosses at the end of each map.
- **Enemy variety** — rushers, spitters, shielded soldiers, turrets, and flying drones.
- **Procedural map seeds** — shareable seed strings so players can compare dungeons.
- **New game modes** — survival, arena challenges, battle-royale-style storm circles, and speedrun timers.
- **Multiplayer (long-term)** — co-op and PvP via the `server/` scaffolding, including squad play and build battles.
- **Leaderboards & stats** — persistent kill/death tracking and global leaderboard support.
- **Audio enhancements** — positional audio, reverb in large rooms, and dynamic music that escalates during combat.
- **Controller support** — gamepad bindings and aim assist.

> Nothing here is guaranteed to ship exactly as described — think of it as the storm cloud on the horizon, and we're heading straight into it.

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
