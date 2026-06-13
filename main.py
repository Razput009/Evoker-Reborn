import pygame
import random
import math
import sys
import os
from dataclasses import dataclass
from typing import List, Optional

pygame.init()

# ====================== CONFIG ======================
ON_ANDROID = "ANDROID_ARGUMENT" in os.environ

if ON_ANDROID:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((480, 854))  # phone-ish portrait window for desktop testing

WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Evoker Reborn - Summon the Legends")
FPS = 60
clock = pygame.time.Clock()

SCALE = WIDTH / 1080.0  # reference width for scaling UI


def sc(v):
    return max(1, int(v * SCALE))


font_small = pygame.font.SysFont("arial", sc(22))
font = pygame.font.SysFont("arial", sc(28))
font_med = pygame.font.SysFont("arial", sc(36), bold=True)
big_font = pygame.font.SysFont("arial", sc(60), bold=True)

# Colors
BG_TOP = (18, 12, 32)
BG_BOTTOM = (45, 20, 60)
ACCENT = (200, 80, 240)
GOLD = (255, 210, 90)
WHITE = (245, 245, 245)
GREEN = (90, 230, 120)
RED = (240, 80, 80)
BLUE = (120, 190, 255)

# Card sizing - 5 columns must fit across the width
CARD_W = (WIDTH - sc(60)) // 5 - sc(10)
CARD_H = int(CARD_W * 1.45)


# ====================== UTIL ======================
def lerp(a, b, t):
    return a + (b - a) * t


def draw_gradient(surface, top_color, bottom_color):
    h = surface.get_height()
    for y in range(h):
        t = y / h
        color = (
            int(lerp(top_color[0], bottom_color[0], t)),
            int(lerp(top_color[1], bottom_color[1], t)),
            int(lerp(top_color[2], bottom_color[2], t)),
        )
        pygame.draw.line(surface, color, (0, y), (surface.get_width(), y))


# ====================== CARD SYSTEM ======================
@dataclass
class CardTemplate:
    name: str
    tribe: str
    max_hp: int
    atk: int
    special: str = ""
    desc: str = ""
    color: tuple = (100, 100, 200)


@dataclass
class Card:
    template: CardTemplate
    hp: int = 0
    display_hp: float = 0.0
    used_burst: bool = False
    lunge: float = 0.0
    flash: float = 0.0

    def __post_init__(self):
        if self.hp == 0:
            self.hp = self.template.max_hp
        self.display_hp = float(self.hp)

    @property
    def name(self):
        return self.template.name

    @property
    def tribe(self):
        return self.template.tribe

    @property
    def atk(self):
        return self.template.atk

    @property
    def max_hp(self):
        return self.template.max_hp

    @property
    def special(self):
        return self.template.special

    @property
    def color(self):
        return self.template.color

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, dmg, plist=None, x=0, y=0):
        if dmg <= 0:
            return 0
        if self.special == "tank":
            dmg = max(1, dmg - 3)
        actual = min(self.hp, dmg)
        self.hp = max(0, self.hp - dmg)
        self.flash = 10
        if plist is not None:
            spawn_hit_particles(plist, x, y, self.color)
        return actual

    def heal(self, amount):
        if self.hp <= 0:
            return
        self.hp = min(self.max_hp, self.hp + amount)


CARD_POOL = [
    CardTemplate("Pikeman", "Dwarf", 16, 7, "", "Steadfast spear-wall defender.", (190, 150, 90)),
    CardTemplate("Ironclad", "Dwarf", 22, 8, "tank", "Heavy armor reduces damage taken.", (170, 170, 190)),
    CardTemplate("Boulder Thrower", "Dwarf", 14, 9, "splash", "Hits the lane beside its target.", (150, 110, 70)),
    CardTemplate("Envoy", "Elf", 10, 11, "snipe", "Strikes true for bonus damage.", (90, 210, 130)),
    CardTemplate("Forest Warden", "Elf", 13, 8, "heal", "Mends the lane beside it.", (70, 190, 110)),
    CardTemplate("Windrunner", "Elf", 9, 13, "burst", "Overwhelming opening strike.", (130, 230, 180)),
    CardTemplate("Throat Cutter", "Orc", 12, 14, "lifesteal", "Drains life from victims.", (210, 70, 70)),
    CardTemplate("Warbreaker", "Orc", 17, 10, "stun", "Crushing blow staggers foes.", (180, 90, 40)),
    CardTemplate("Skullcrusher", "Orc", 15, 16, "", "Pure brute force.", (160, 50, 50)),
    CardTemplate("Fire Drake", "Dragon", 17, 12, "splash", "Scorches the adjacent lane.", (230, 110, 30)),
    CardTemplate("Frost Wyrm", "Dragon", 19, 9, "stun", "Icy breath chills reflexes.", (120, 200, 230)),
    CardTemplate("Bone Reaper", "Undead", 13, 13, "lifesteal", "Feeds on the wounds it inflicts.", (140, 140, 100)),
    CardTemplate("Wraith", "Undead", 9, 12, "snipe", "Unerring spectral strike.", (110, 90, 160)),
    CardTemplate("Stone Golem", "Neutral", 26, 6, "tank", "Unbreakable wall of rock.", (150, 150, 170)),
    CardTemplate("Shadow Assassin", "Neutral", 9, 17, "snipe", "Strikes from the dark.", (100, 60, 150)),
    CardTemplate("Mystic Healer", "Neutral", 11, 6, "heal", "Restores a neighbor's health.", (210, 200, 140)),
    CardTemplate("Direwolf", "Beast", 11, 14, "burst", "Pounces with savage force.", (100, 80, 60)),
]


def make_card(template: CardTemplate) -> Card:
    return Card(template=template)


# ====================== PARTICLES & FX ======================
particles = []
floating_texts = []


def spawn_hit_particles(plist, x, y, color, count=12):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 5) * SCALE
        plist.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.randint(20, 40),
            "max_life": 40,
            "color": color,
            "size": sc(random.randint(2, 5)),
        })


def spawn_floating_text(text, x, y, color):
    floating_texts.append({"text": text, "x": x, "y": y, "life": 45, "color": color})


def update_particles():
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.15 * SCALE
        p["life"] -= 1
        if p["life"] <= 0:
            particles.remove(p)

    for t in floating_texts[:]:
        t["y"] -= 1.2 * SCALE
        t["life"] -= 1
        if t["life"] <= 0:
            floating_texts.remove(t)


def draw_particles(surface):
    for p in particles:
        alpha = max(0, int(255 * (p["life"] / p["max_life"])))
        s = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*p["color"], alpha), (p["size"], p["size"]), p["size"])
        surface.blit(s, (p["x"] - p["size"], p["y"] - p["size"]))

    for t in floating_texts:
        alpha = max(0, int(255 * (t["life"] / 45)))
        surf = font_med.render(t["text"], True, t["color"])
        surf.set_alpha(alpha)
        surface.blit(surf, (t["x"] - surf.get_width() // 2, t["y"]))


# ====================== BATTLE ENGINE ======================
class BattleEngine:
    def __init__(self, player_deck: List[Card], enemy_deck: List[Card]):
        self.p = player_deck
        self.e = enemy_deck
        self.turn = 0
        self.phase = "pause"
        self.timer = 45
        self.finished = False
        self.winner = None

    def all_dead(self, deck):
        return all(not c.is_alive() for c in deck)

    def update(self):
        if self.finished:
            return

        self.timer -= 1
        if self.timer > 0:
            return

        if self.phase == "pause":
            if self.all_dead(self.p) or self.all_dead(self.e):
                self.finished = True
                p_remaining = sum(c.hp for c in self.p)
                e_remaining = sum(c.hp for c in self.e)
                self.winner = "player" if p_remaining >= e_remaining and not self.all_dead(self.p) else "enemy"
                if self.all_dead(self.p) and self.all_dead(self.e):
                    self.winner = "player" if p_remaining > e_remaining else "enemy"
                return
            self.turn += 1
            self.phase = "lunge"
            self.timer = 12
            for c in self.p + self.e:
                if c.is_alive():
                    c.lunge = 0

        elif self.phase == "lunge":
            self.phase = "impact"
            self.timer = 6
            self.do_combat()

        elif self.phase == "impact":
            self.phase = "settle"
            self.timer = 25

        elif self.phase == "settle":
            self.phase = "pause"
            self.timer = 30

    def do_combat(self):
        for i in range(5):
            p, e = self.p[i], self.e[i]
            if not (p.is_alive() and e.is_alive()):
                continue

            px, py = lane_pos(i, True)
            ex, ey = lane_pos(i, False)

            p.lunge = 18
            e.lunge = -18

            p_stunned = p.special == "stun" and random.random() < 0.25
            e_stunned = e.special == "stun" and random.random() < 0.25

            p_dmg = p.atk
            e_dmg = e.atk

            if p.special == "burst" and not p.used_burst:
                p_dmg += 5
                p.used_burst = True
            if e.special == "burst" and not e.used_burst:
                e_dmg += 5
                e.used_burst = True

            if p.special == "snipe":
                p_dmg += 3
            if e.special == "snipe":
                e_dmg += 3

            dealt = e.take_damage(p_dmg, particles, ex + CARD_W // 2, ey + CARD_H // 2)
            if dealt > 0:
                spawn_floating_text(f"-{dealt}", ex + CARD_W // 2, ey, RED)
            if p.special == "lifesteal" and dealt > 0:
                p.heal(dealt // 2)
                spawn_floating_text(f"+{dealt // 2}", px + CARD_W // 2, py, GREEN)

            if p.special == "splash" and i + 1 < 5 and self.e[i + 1].is_alive():
                st = self.e[i + 1]
                sx, sy = lane_pos(i + 1, False)
                d2 = st.take_damage(p.atk // 2, particles, sx + CARD_W // 2, sy + CARD_H // 2)
                if d2 > 0:
                    spawn_floating_text(f"-{d2}", sx + CARD_W // 2, sy, RED)

            if not e_stunned:
                dealt2 = p.take_damage(e_dmg, particles, px + CARD_W // 2, py + CARD_H // 2)
                if dealt2 > 0:
                    spawn_floating_text(f"-{dealt2}", px + CARD_W // 2, py, RED)
                if e.special == "lifesteal" and dealt2 > 0:
                    e.heal(dealt2 // 2)
                    spawn_floating_text(f"+{dealt2 // 2}", ex + CARD_W // 2, ey, GREEN)

            if e.special == "splash" and i + 1 < 5 and self.p[i + 1].is_alive():
                st = self.p[i + 1]
                sx, sy = lane_pos(i + 1, True)
                d2 = st.take_damage(e.atk // 2, particles, sx + CARD_W // 2, sy + CARD_H // 2)
                if d2 > 0:
                    spawn_floating_text(f"-{d2}", sx + CARD_W // 2, sy, RED)

            if p_stunned:
                spawn_floating_text("STUNNED", ex + CARD_W // 2, ey - sc(20), GOLD)
            if e_stunned:
                spawn_floating_text("STUNNED", px + CARD_W // 2, py - sc(20), GOLD)

        for i in range(5):
            if self.p[i].is_alive() and self.p[i].special == "heal" and i + 1 < 5 and self.p[i + 1].is_alive():
                self.p[i + 1].heal(3)
            if self.e[i].is_alive() and self.e[i].special == "heal" and i + 1 < 5 and self.e[i + 1].is_alive():
                self.e[i + 1].heal(3)


# ====================== LAYOUT ======================
def lane_margin():
    return (WIDTH - 5 * CARD_W) // 6


def lane_pos(i, is_player):
    m = lane_margin()
    x = m + i * (CARD_W + m)
    y = int(HEIGHT * 0.55) if is_player else int(HEIGHT * 0.06)
    return x, y


def grid_pos(idx):
    """2-column grid for deck select."""
    m = (WIDTH - 2 * CARD_W) // 3
    col = idx % 2
    row = idx // 2
    x = m + col * (CARD_W + m)
    y = sc(120) + row * (CARD_H + sc(16))
    return x, y


# ====================== RENDERING ======================
def draw_card(surface, card: Card, x, y, selected=False, show_hp=True):
    offset_y = 0
    if card.lunge != 0:
        offset_y = int((-card.lunge if card.lunge > 0 else card.lunge) * 0.4)
    draw_y = y + offset_y

    card.display_hp = lerp(card.display_hp, card.hp, 0.18)

    base_color = card.color
    if card.flash > 0:
        base_color = tuple(min(255, c + 120) for c in base_color)
        card.flash -= 1

    faded = not card.is_alive()

    shadow = pygame.Surface((CARD_W + sc(8), CARD_H + sc(8)), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 90), shadow.get_rect(), border_radius=sc(14))
    surface.blit(shadow, (x - sc(4), draw_y + sc(6)))

    card_surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(card_surf, base_color, card_surf.get_rect(), border_radius=sc(14))

    highlight = pygame.Surface((CARD_W, CARD_H // 2), pygame.SRCALPHA)
    pygame.draw.rect(highlight, (255, 255, 255, 40), highlight.get_rect(), border_radius=sc(14))
    card_surf.blit(highlight, (0, 0))

    border_color = GOLD if selected else (255, 255, 255)
    pygame.draw.rect(card_surf, border_color, card_surf.get_rect(), sc(3), border_radius=sc(14))

    if faded:
        card_surf.set_alpha(90)

    surface.blit(card_surf, (x, draw_y))

    if faded:
        pygame.draw.line(surface, (255, 80, 80), (x + sc(20), draw_y + sc(20)), (x + CARD_W - sc(20), draw_y + CARD_H - sc(20)), sc(4))
        pygame.draw.line(surface, (255, 80, 80), (x + CARD_W - sc(20), draw_y + sc(20)), (x + sc(20), draw_y + CARD_H - sc(20)), sc(4))

    name_surf = font_small.render(card.name, True, WHITE)
    surface.blit(name_surf, (x + sc(8), draw_y + sc(6)))

    tribe_surf = font_small.render(card.tribe, True, (230, 220, 150))
    surface.blit(tribe_surf, (x + sc(8), draw_y + sc(28)))

    if card.special:
        spec_surf = font_small.render(card.special.upper(), True, (255, 230, 180))
        surface.blit(spec_surf, (x + sc(8), draw_y + sc(48)))

    atk_surf = font.render(f"{card.atk} ATK", True, GOLD)
    surface.blit(atk_surf, (x + sc(8), draw_y + CARD_H - sc(60)))

    if show_hp:
        bar_w = CARD_W - sc(16)
        bar_h = sc(14)
        bar_x = x + sc(8)
        bar_y = draw_y + CARD_H - sc(28)
        pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=sc(6))
        ratio = max(0, card.display_hp / card.max_hp)
        fill_w = int(bar_w * ratio)
        hp_color = GREEN if ratio > 0.5 else (GOLD if ratio > 0.25 else RED)
        if fill_w > 0:
            pygame.draw.rect(surface, hp_color, (bar_x, bar_y, fill_w, bar_h), border_radius=sc(6))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), sc(2), border_radius=sc(6))
        hp_text = font_small.render(f"{max(0, card.hp)}/{card.max_hp}", True, WHITE)
        surface.blit(hp_text, (bar_x + bar_w // 2 - hp_text.get_width() // 2, bar_y - sc(2)))


def draw_button(surface, rect, text, hovered=False, enabled=True):
    if not enabled:
        color = (90, 90, 100)
    else:
        color = (230, 130, 255) if hovered else ACCENT
    pygame.draw.rect(surface, color, rect, border_radius=sc(10))
    pygame.draw.rect(surface, WHITE, rect, sc(2), border_radius=sc(10))
    txt_color = WHITE if enabled else (170, 170, 170)
    txt = font.render(text, True, txt_color)
    surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))


# ====================== GAME ======================
class Game:
    def __init__(self):
        self.state = "menu"
        self.pool_selection: List[CardTemplate] = []
        self.selected_indices = set()
        self.player_deck: List[Card] = []
        self.enemy_deck: List[Card] = []
        self.engine: Optional[BattleEngine] = None
        self.bg_surface = pygame.Surface((WIDTH, HEIGHT))
        draw_gradient(self.bg_surface, BG_TOP, BG_BOTTOM)
        self.refresh_pool()

    def refresh_pool(self):
        self.pool_selection = random.sample(CARD_POOL, 10)
        self.selected_indices = set()

    def start_battle(self):
        self.player_deck = [make_card(self.pool_selection[i]) for i in self.selected_indices]
        enemy_templates = random.sample(CARD_POOL, 5)
        self.enemy_deck = [make_card(t) for t in enemy_templates]
        self.engine = BattleEngine(self.player_deck, self.enemy_deck)
        self.state = "battle"
        particles.clear()
        floating_texts.clear()

    def reset(self):
        self.state = "menu"
        self.refresh_pool()
        self.engine = None
        particles.clear()
        floating_texts.clear()


def main():
    game = Game()
    running = True

    while running:
        tap_pos = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                tap_pos = event.pos
            elif event.type == pygame.FINGERDOWN:
                tap_pos = (int(event.x * WIDTH), int(event.y * HEIGHT))
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_AC_BACK):
                    if game.state == "menu":
                        running = False
                    else:
                        game.reset()

        screen.blit(game.bg_surface, (0, 0))

        # ---------------- MENU ----------------
        if game.state == "menu":
            title = big_font.render("EVOKER REBORN", True, ACCENT)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, int(HEIGHT * 0.25)))
            subtitle = font.render("Summon the Legends", True, (200, 200, 220))
            screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, int(HEIGHT * 0.25) + sc(80)))

            btn_w, btn_h = sc(320), sc(80)
            btn_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, int(HEIGHT * 0.5), btn_w, btn_h)
            draw_button(screen, btn_rect, "Build Your Deck")
            if tap_pos and btn_rect.collidepoint(tap_pos):
                game.state = "deck_select"

        # ---------------- DECK SELECT ----------------
        elif game.state == "deck_select":
            title = font_med.render("Choose 5 Champions", True, WHITE)
            screen.blit(title, (sc(20), sc(20)))

            count_text = font.render(f"Selected: {len(game.selected_indices)}/5", True, GOLD)
            screen.blit(count_text, (sc(20), sc(70)))

            for idx, tmpl in enumerate(game.pool_selection):
                x, y = grid_pos(idx)
                temp_card = make_card(tmpl)
                selected = idx in game.selected_indices
                rect = pygame.Rect(x, y, CARD_W, CARD_H)
                draw_card(screen, temp_card, x, y, selected=selected, show_hp=False)

                if tap_pos and rect.collidepoint(tap_pos):
                    if selected:
                        game.selected_indices.discard(idx)
                    elif len(game.selected_indices) < 5:
                        game.selected_indices.add(idx)

            bottom_y = HEIGHT - sc(100)
            reroll_rect = pygame.Rect(sc(20), bottom_y, sc(220), sc(70))
            draw_button(screen, reroll_rect, "Reroll")
            if tap_pos and reroll_rect.collidepoint(tap_pos):
                game.refresh_pool()

            ready = len(game.selected_indices) == 5
            begin_rect = pygame.Rect(WIDTH - sc(20) - sc(280), bottom_y, sc(280), sc(70))
            draw_button(screen, begin_rect, "BEGIN BATTLE", enabled=ready)
            if tap_pos and ready and begin_rect.collidepoint(tap_pos):
                game.start_battle()

        # ---------------- BATTLE ----------------
        elif game.state == "battle":
            engine = game.engine
            engine.update()
            update_particles()

            turn_surf = font_med.render(f"TURN {engine.turn}", True, GOLD)
            screen.blit(turn_surf, (WIDTH // 2 - turn_surf.get_width() // 2, int(HEIGHT * 0.46)))

            for i, card in enumerate(game.player_deck):
                x, y = lane_pos(i, True)
                draw_card(screen, card, x, y)
            for i, card in enumerate(game.enemy_deck):
                x, y = lane_pos(i, False)
                draw_card(screen, card, x, y)

            draw_particles(screen)

            if engine.finished:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))

                if engine.winner == "player":
                    msg = "VICTORY!"
                    color = GREEN
                else:
                    msg = "DEFEAT"
                    color = RED

                msg_surf = big_font.render(msg, True, color)
                screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, int(HEIGHT * 0.4)))

                btn_w, btn_h = sc(280), sc(80)
                again_rect = pygame.Rect(WIDTH // 2 - btn_w // 2, int(HEIGHT * 0.55), btn_w, btn_h)
                draw_button(screen, again_rect, "Play Again")
                if tap_pos and again_rect.collidepoint(tap_pos):
                    game.reset()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
