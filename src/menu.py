import math
import sys
import pygame as pg
import game_state
from textures import get_weapon_image

_weapon_icon_cache = {}


def _get_weapon_icon(name, target_w=170):
    key = (name, target_w)
    if key not in _weapon_icon_cache:
        img = get_weapon_image(name)
        if img is None:
            _weapon_icon_cache[key] = False
        else:
            rect = img.get_bounding_rect(min_alpha=8)
            if rect.width <= 0 or rect.height <= 0:
                _weapon_icon_cache[key] = False
            else:
                weapon = img.subsurface(rect)
                scale = target_w / weapon.get_width()
                _weapon_icon_cache[key] = pg.transform.smoothscale(
                    weapon, (target_w, max(1, int(weapon.get_height() * scale)))
                )
    return _weapon_icon_cache[key]

pg.init()

W = 1280
H = 720
screen = pg.display.set_mode((W, H), pg.DOUBLEBUF | pg.SCALED)
pg.display.set_caption("HexForge")
clock = pg.time.Clock()

BG_DARK = (18, 18, 24)
BG_PANEL = (25, 25, 35)
BG_PANEL_LIGHT = (32, 32, 45)
ACCENT = (230, 150, 40)
ACCENT_DIM = (160, 100, 28)
ACCENT_BRIGHT = (255, 190, 60)
TEXT_WHITE = (240, 240, 240)
TEXT_DIM = (140, 140, 150)
TEXT_GREEN = (80, 220, 100)
TEXT_RED = (220, 80, 70)
BORDER_COLOR = (60, 60, 75)
BORDER_HOVER = (120, 120, 140)

try:
    font_title = pg.font.SysFont("segoeui", 72, bold=True)
    font_big = pg.font.SysFont("segoeui", 36, bold=True)
    font_med = pg.font.SysFont("segoeui", 24)
    font_small = pg.font.SysFont("segoeui", 18)
    font_tiny = pg.font.SysFont("segoeui", 14)
except Exception:
    font_title = pg.font.SysFont("arial", 72, bold=True)
    font_big = pg.font.SysFont("arial", 36, bold=True)
    font_med = pg.font.SysFont("arial", 24)
    font_small = pg.font.SysFont("arial", 18)
    font_tiny = pg.font.SysFont("arial", 14)


def draw_hex_bg(t):
    for row in range(0, H + 40, 36):
        for col in range(0, W + 40, 42):
            offset = 21 if (row // 36) % 2 else 0
            cx = col + offset
            cy = row
            pulse = math.sin(t * 0.0008 + cx * 0.005 + cy * 0.003) * 0.5 + 0.5
            alpha = int(12 + pulse * 8)
            r, g, b = BG_DARK
            cr = min(255, r + alpha)
            cg = min(255, g + alpha)
            cb = min(255, b + alpha + int(pulse * 15))
            pts = []
            for i in range(6):
                a = math.pi / 3 * i + math.pi / 6
                pts.append((cx + 18 * math.cos(a), cy + 18 * math.sin(a)))
            pg.draw.polygon(screen, (cr, cg, cb), pts)
            pg.draw.polygon(screen, (cr + 8, cg + 8, cb + 10), pts, 1)


class Button:
    def __init__(self, x, y, w, h, text, font_ref=None):
        self.rect = pg.Rect(x, y, w, h)
        self.text = text
        self.font_ref = font_ref or font_med
        self.hovered = False
        self.click_anim = 0

    def update(self, mx, my):
        self.hovered = self.rect.collidepoint(mx, my)

    def draw(self):
        if self.click_anim > 0:
            self.click_anim = max(0, self.click_anim - 0.05)

        border_c = ACCENT if self.hovered else BORDER_COLOR
        bg = BG_PANEL_LIGHT if self.hovered else BG_PANEL

        if self.click_anim > 0:
            shrink = int(self.click_anim * 4)
            r = self.rect.inflate(-shrink * 2, -shrink * 2)
        else:
            r = self.rect

        pg.draw.rect(screen, bg, r, border_radius=6)
        pg.draw.rect(screen, border_c, r, 2, border_radius=6)

        if self.hovered:
            glow = pg.Surface((r.width, 2), pg.SRCALPHA)
            glow.fill((*ACCENT, 40))
            screen.blit(glow, (r.x, r.y))

        txt = self.font_ref.render(self.text, True, ACCENT if self.hovered else TEXT_WHITE)
        tx = r.x + (r.width - txt.get_width()) // 2
        ty = r.y + (r.height - txt.get_height()) // 2
        screen.blit(txt, (tx, ty))

    def clicked(self, mx, my):
        if self.rect.collidepoint(mx, my):
            self.click_anim = 1.0
            return True
        return False


class ShopItem:
    def __init__(self, x, y, w, name, price, desc, owned=False, is_upgrade=False):
        self.rect = pg.Rect(x, y, w, 90)
        self.name = name
        self.price = price
        self.desc = desc
        self.owned = owned
        self.is_upgrade = is_upgrade
        self.btn = Button(x + w - 120, y + 30, 110, 32,
                          "OWNED" if owned else f"${price}",
                          font_small)
        self.btn.rect.h = 32

    def update(self, mx, my):
        self.btn.update(mx, my)

    def draw(self):
        panel = BG_PANEL_LIGHT if self.btn.hovered else BG_PANEL
        pg.draw.rect(screen, panel, self.rect, border_radius=8)
        pg.draw.rect(screen, BORDER_COLOR if not self.owned else (60, 80, 60), self.rect, 1, border_radius=8)

        name_c = TEXT_GREEN if self.owned else TEXT_WHITE
        nt = font_med.render(self.name, True, name_c)
        screen.blit(nt, (self.rect.x + 14, self.rect.y + 10))

        dt = font_tiny.render(self.desc, True, TEXT_DIM)
        screen.blit(dt, (self.rect.x + 14, self.rect.y + 42))

        if not self.owned:
            self.btn.draw()

    def clicked(self, mx, my):
        if self.owned:
            return False
        return self.btn.clicked(mx, my)


def draw_title_text(t):
    title = "Hexforge"
    tx = W // 2 - 120
    ty = 80
    for i, ch in enumerate(title):
        bounce = math.sin(t * 0.003 + i * 0.4) * 4
        color = (ACCENT[0], min(255, ACCENT[1] + i * 8), ACCENT[2])
        s = font_title.render(ch, True, color)
        screen.blit(s, (tx + i * 55, ty + int(bounce)))


def draw_coin_icon(x, y, size=18):
    pg.draw.circle(screen, ACCENT_BRIGHT, (x, y), size)
    pg.draw.circle(screen, ACCENT, (x, y), size, 2)
    d = font_tiny.render("$", True, BG_DARK)
    screen.blit(d, (x - d.get_width() // 2, y - d.get_height() // 2))


def draw_decorative_icon(x, y, t):
    pulse = math.sin(t * 0.002) * 0.15 + 0.85
    r1 = int(30 * pulse)
    r2 = int(20 * pulse)
    r3 = int(12 * pulse)
    pg.draw.circle(screen, (ACCENT[0], ACCENT[1], ACCENT[2]), (x, y), r1, 2)
    pg.draw.circle(screen, (ACCENT[0], ACCENT[1] - 20, ACCENT[2]), (x, y - 8), r2, 2)
    pg.draw.line(screen, ACCENT, (x - 14, y + 10), (x + 14, y + 10), 2)
    pg.draw.line(screen, ACCENT, (x - 10, y + 16), (x + 10, y + 16), 2)
    pg.draw.line(screen, ACCENT, (x - 6, y + 22), (x + 6, y + 22), 2)
    inner = font_small.render("F", True, ACCENT_BRIGHT)
    screen.blit(inner, (x - inner.get_width() // 2, y - inner.get_height() // 2 - 8))


def main_menu():
    btn_play = Button(W // 2 - 120, 260, 240, 56, "Play", font_big)
    btn_loadout = Button(W // 2 - 100, 340, 200, 46, "Loadout")
    btn_shop = Button(20, H - 80, 160, 50, "Shop", font_big)
    btn_quit = Button(20, 20, 100, 36, "Quit", font_small)
    buttons = [btn_play, btn_loadout, btn_shop, btn_quit]

    while True:
        dt_ms = clock.tick(60)
        t = pg.time.get_ticks()
        mx, my = pg.mouse.get_pos()

        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                return "quit"
            if ev.type == pg.KEYDOWN and ev.key == pg.K_ESCAPE:
                return "quit"
            if ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_play.clicked(mx, my):
                    return "play"
                if btn_loadout.clicked(mx, my):
                    return "loadout"
                if btn_shop.clicked(mx, my):
                    return "shop"
                if btn_quit.clicked(mx, my):
                    return "quit"

        screen.fill(BG_DARK)
        draw_hex_bg(t)
        draw_title_text(t)
        draw_decorative_icon(W - 70, 70, t)

        money = game_state.get_money()
        draw_coin_icon(W - 160, H - 45, 14)
        mt = font_med.render(f": {money}", True, ACCENT_BRIGHT)
        screen.blit(mt, (W - 142, H - 58))

        for b in buttons:
            b.update(mx, my)
            b.draw()

        hint = font_tiny.render("Press 1-4 to switch weapons in game", True, TEXT_DIM)
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))

        pg.display.flip()


def shop_screen():
    items = []
    x_start = 40
    y_start = 80
    col_w = 380
    col_gap = 20
    row_gap = 15

    owned = game_state.get_owned()
    upgrades = game_state.get_upgrades("AK47") + game_state.get_upgrades("Glock19") + game_state.get_upgrades("Grenade")

    weapon_defs = [
        ("AK47", 0, "Primary assault rifle - 30 rounds"),
        ("Glock19", 500, "Secondary pistol - semi-auto"),
        ("Knife", 300, "Melee weapon - close range"),
        ("Grenade", 200, "Throwable explosive - AOE damage"),
    ]
    for i, (name, price, desc) in enumerate(weapon_defs):
        col = i % 2
        row = i // 2
        ix = x_start + col * (col_w + col_gap)
        iy = y_start + row * (110 + row_gap)
        items.append(ShopItem(ix, iy, col_w, name, price, desc, owned=(name in owned)))

    upgrade_defs = [
        ("Extended Mag", 400, "+15 AK47 mag / +8 Glock19 mag", "AK47"),
        ("Damage Boost", 600, "+10 AK47 damage / +8 Glock19", "AK47"),
        ("Rapid Fire", 500, "Faster fire rate for AK47/Glock19", "AK47"),
        ("Grenade: Extra Nades", 250, "+2 grenades per purchase", "Grenade"),
        ("Grenade: Blast Radius", 500, "Larger explosion radius", "Grenade"),
        ("Grenade: More Damage", 450, "+25 explosion damage", "Grenade"),
    ]
    for i, (name, price, desc, weapon) in enumerate(upgrade_defs):
        key = f"{weapon}:{name}"
        col = i % 2
        row = (i // 2) + 2
        ix = x_start + col * (col_w + col_gap)
        iy = y_start + row * (110 + row_gap)
        items.append(ShopItem(ix, iy, col_w, name, price, desc, owned=(key in upgrades or name in upgrades), is_upgrade=True))

    btn_back = Button(20, 20, 100, 36, "Back", font_small)
    msg_text = ""
    msg_timer = 0.0
    msg_color = TEXT_GREEN

    scroll_y = 0
    max_scroll = max(0, (len(items) // 2 + 1) * 125 - (H - 160))

    while True:
        dt_ms = clock.tick(60)
        t = pg.time.get_ticks()
        mx, my = pg.mouse.get_pos()

        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                return "quit"
            if ev.type == pg.KEYDOWN:
                if ev.key == pg.K_ESCAPE:
                    return "menu"
            if ev.type == pg.MOUSEBUTTONDOWN:
                if ev.button == 1:
                    if btn_back.clicked(mx, my):
                        return "menu"
                    for item in items:
                        if item.clicked(mx, my):
                            if item.is_upgrade:
                                weapon_name = "AK47"
                                for wd_name, wd_price, wd_desc in weapon_defs:
                                    if wd_name in item.name or (item.name.startswith("Grenade:") and wd_name == "Grenade"):
                                        weapon_name = wd_name
                                        break
                                if item.name.startswith("Grenade:"):
                                    upgrade_name = item.name.replace("Grenade: ", "")
                                    if upgrade_name == "Extra Nades":
                                        ok, msg = game_state.buy_upgrade("Grenade", "Extra Nades")
                                        if ok:
                                            game_state.add_grenades(2)
                                        else:
                                            pass
                                    else:
                                        ok, msg = game_state.buy_upgrade("Grenade", upgrade_name)
                                else:
                                    ok, msg = game_state.buy_upgrade(weapon_name, item.name)
                                msg_text = msg
                                msg_color = TEXT_GREEN if ok else TEXT_RED
                                msg_timer = 2.0
                            else:
                                ok, msg = game_state.buy_weapon(item.name)
                                msg_text = msg
                                msg_color = TEXT_GREEN if ok else TEXT_RED
                                msg_timer = 2.0
                            if ok:
                                owned = game_state.get_owned()
                                upgrades = game_state.get_upgrades("AK47") + game_state.get_upgrades("Glock19") + game_state.get_upgrades("Grenade")
                                for it in items:
                                    if it.name in owned:
                                        it.owned = True
                                        it.btn.text = "OWNED"
                                    full_key = it.name
                                    if it.is_upgrade:
                                        if full_key in upgrades:
                                            it.owned = True
                                            it.btn.text = "OWNED"
                if ev.button == 4:
                    scroll_y = max(0, scroll_y - 30)
                if ev.button == 5:
                    scroll_y = min(max_scroll, scroll_y + 30)

        if msg_timer > 0:
            msg_timer -= dt_ms / 1000.0

        screen.fill(BG_DARK)
        draw_hex_bg(t)

        title = font_big.render("SHOP", True, ACCENT)
        screen.blit(title, (W // 2 - title.get_width() // 2, 25))

        money = game_state.get_money()
        draw_coin_icon(W - 160, 45, 14)
        mt = font_med.render(f": {money}", True, ACCENT_BRIGHT)
        screen.blit(mt, (W - 142, 32))

        clip_rect = pg.Rect(0, 75, W, H - 90)
        screen.set_clip(clip_rect)

        for item in items:
            adjusted = pg.Rect(item.rect.x, item.rect.y - scroll_y, item.rect.width, item.rect.height)
            if adjusted.bottom > 75 and adjusted.top < H:
                orig_rect = item.rect
                item.rect = adjusted
                item.btn.rect = pg.Rect(item.btn.rect.x, item.btn.rect.y - scroll_y, item.btn.rect.width, item.btn.rect.height)
                item.update(mx, my)
                item.draw()
                item.rect = orig_rect
                item.btn.rect = pg.Rect(item.btn.rect.x, item.btn.rect.y + scroll_y, item.btn.rect.width, item.btn.rect.height)

        screen.set_clip(None)

        if msg_timer > 0:
            msg_bg = pg.Surface((400, 36), pg.SRCALPHA)
            msg_bg.fill((0, 0, 0, 180))
            screen.blit(msg_bg, (W // 2 - 200, H - 50))
            msg_s = font_small.render(msg_text, True, msg_color)
            screen.blit(msg_s, (W // 2 - msg_s.get_width() // 2, H - 46))

        btn_back.update(mx, my)
        btn_back.draw()
        pg.display.flip()


def loadout_screen():
    btn_back = Button(20, 20, 100, 36, "Back", font_small)
    weapon_cards = []

    card_w = 280
    card_h = 320
    gap = 30
    total_w = 4 * card_w + 3 * gap
    start_x = (W - total_w) // 2

    weapon_info = [
        ("AK47", "Primary", "Assault Rifle", "30 ammo", (130, 85, 45)),
        ("Glock19", "Secondary", "Pistol", "17 ammo", (65, 62, 55)),
        ("Knife", "Melee", "Close Range", "Infinite", (190, 195, 200)),
        ("Grenade", "Explosive", "Throwable", "3 nades", (70, 85, 55)),
    ]
    for i, (name, slot, desc, ammo, color) in enumerate(weapon_info):
        cx = start_x + i * (card_w + gap)
        cy = 120
        weapon_cards.append((pg.Rect(cx, cy, card_w, card_h), name, slot, desc, ammo, color))

    while True:
        dt_ms = clock.tick(60)
        t = pg.time.get_ticks()
        mx, my = pg.mouse.get_pos()

        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                return "quit"
            if ev.type == pg.KEYDOWN:
                if ev.key == pg.K_ESCAPE:
                    return "menu"
            if ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
                if btn_back.clicked(mx, my):
                    return "menu"

        screen.fill(BG_DARK)
        draw_hex_bg(t)

        title = font_big.render("LOADOUT", True, ACCENT)
        screen.blit(title, (W // 2 - title.get_width() // 2, 30))

        owned = game_state.get_owned()
        upgrades_list = game_state.get_upgrades("AK47") + game_state.get_upgrades("Glock19") + game_state.get_upgrades("Grenade")

        for rect, name, slot, desc, ammo, color in weapon_cards:
            is_owned = name in owned
            panel_c = BG_PANEL_LIGHT if rect.collidepoint(mx, my) else BG_PANEL
            if not is_owned:
                panel_c = (20, 20, 28)
            pg.draw.rect(screen, panel_c, rect, border_radius=10)
            border_c = ACCENT if rect.collidepoint(mx, my) else BORDER_COLOR
            pg.draw.rect(screen, border_c if is_owned else (50, 50, 60), rect, 2, border_radius=10)

            slot_c = ACCENT if is_owned else TEXT_DIM
            slot_s = font_tiny.render(slot.upper(), True, slot_c)
            screen.blit(slot_s, (rect.x + 14, rect.y + 12))

            name_c = TEXT_WHITE if is_owned else TEXT_DIM
            name_s = font_big.render(name, True, name_c)
            screen.blit(name_s, (rect.x + 14, rect.y + 30))

            desc_s = font_small.render(desc, True, TEXT_DIM)
            screen.blit(desc_s, (rect.x + 14, rect.y + 70))

            ammo_s = font_med.render(ammo, True, ACCENT_BRIGHT if is_owned else TEXT_DIM)
            screen.blit(ammo_s, (rect.x + 14, rect.y + 100))

            icon_cx = rect.x + rect.w // 2
            icon_cy = rect.y + 180
            if name in ("AK47", "Glock19"):
                weapon_icon = _get_weapon_icon("Gun" if name == "AK47" else "Glock19")
                if weapon_icon:
                    screen.blit(weapon_icon, (icon_cx - weapon_icon.get_width() // 2, icon_cy - weapon_icon.get_height() // 2))
                elif name == "AK47":
                    pg.draw.rect(screen, color, (icon_cx - 50, icon_cy - 8, 100, 16), border_radius=3)
                    pg.draw.rect(screen, (color[0] - 20, color[1] - 15, color[2] - 10), (icon_cx - 60, icon_cy + 5, 40, 20), border_radius=3)
                    pg.draw.rect(screen, (45, 42, 38), (icon_cx + 40, icon_cy - 6, 30, 12), border_radius=2)
                else:
                    pg.draw.rect(screen, color, (icon_cx - 35, icon_cy - 10, 70, 18), border_radius=3)
                    pg.draw.rect(screen, (color[0] - 10, color[1] - 10, color[2] - 8), (icon_cx - 25, icon_cy + 5, 25, 28), border_radius=3)
            elif name == "Knife":
                pts = [(icon_cx, icon_cy - 40), (icon_cx + 5, icon_cy - 38), (icon_cx + 3, icon_cy + 15), (icon_cx - 3, icon_cy + 15)]
                pg.draw.polygon(screen, color, pts)
                pg.draw.rect(screen, (100, 72, 40), (icon_cx - 8, icon_cy + 15, 16, 25), border_radius=2)
            elif name == "Grenade":
                pg.draw.rect(screen, color, (icon_cx - 14, icon_cy - 15, 28, 30), border_radius=6)
                pg.draw.rect(screen, (90, 85, 70), (icon_cx - 8, icon_cy - 22, 16, 8), border_radius=2)
                for i in range(3):
                    pg.draw.line(screen, (55, 70, 42), (icon_cx - 12, icon_cy - 12 + i * 10), (icon_cx + 12, icon_cy - 12 + i * 10), 1)

            if is_owned and upgrades_list:
                up_text = [u for u in upgrades_list if name in u or (name == "Grenade" and "Grenade" in u)]
                if up_text:
                    up_s = font_tiny.render(f"+{len(up_text)} upgrades", True, TEXT_GREEN)
                    screen.blit(up_s, (rect.x + 14, rect.y + rect.h - 25))
            elif not is_owned:
                lock_s = font_small.render("LOCKED", True, TEXT_RED)
                screen.blit(lock_s, (rect.x + 14, rect.y + rect.h - 25))

        hint = font_tiny.render("1: AK47  |  2: Glock  |  3: Knife  |  4: Grenade", True, TEXT_DIM)
        screen.blit(hint, (W // 2 - hint.get_width() // 2, H - 30))

        btn_back.update(mx, my)
        btn_back.draw()
        pg.display.flip()


def run():
    global screen
    state = "menu"
    while True:
        if state == "menu":
            result = main_menu()
        elif state == "shop":
            result = shop_screen()
        elif state == "loadout":
            result = loadout_screen()
        elif state == "play":
            screen.fill(BG_DARK)
            load_txt = font_med.render("Loading textures...", True, TEXT_WHITE)
            screen.blit(load_txt, (W // 2 - load_txt.get_width() // 2, H // 2))
            pg.display.flip()
            from textures import get_texture, TEXTURE_NAMES
            for _name in TEXTURE_NAMES:
                get_texture(_name)
            pg.quit()
            import window
            window.run()
            pg.init()
            screen = pg.display.set_mode((W, H), pg.DOUBLEBUF | pg.SCALED)
            pg.display.set_caption("HexForge")
            result = "menu"
        elif state == "quit":
            pg.quit()
            sys.exit()
        else:
            result = "quit"

        if result == "quit":
            pg.quit()
            sys.exit()
        elif result == "play":
            state = "play"
        elif result == "menu":
            state = "menu"
        elif result == "shop":
            state = "shop"
        elif result == "loadout":
            state = "loadout"


if __name__ == "__main__":
    run()
