import pygame as pg

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 240

WINDOW_TITLE = "HexForge"

# --------------------------------------------------------------------------
# Initialize
# --------------------------------------------------------------------------

pg.init()

screen = pg.display.set_mode(
    (SCREEN_WIDTH, SCREEN_HEIGHT),
    pg.RESIZABLE | pg.DOUBLEBUF,
)

pg.display.set_caption(WINDOW_TITLE)

clock = pg.time.Clock()

# --------------------------------------------------------------------------
# Main Loop
# --------------------------------------------------------------------------

running = True

while running:
    dt = clock.tick(FPS) / 1000.0  # Seconds since last frame

    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    # Update
    # update(dt)

    # Draw
    screen.fill((20, 20, 20))
    # render(screen)

    pg.display.flip()

pg.quit()
