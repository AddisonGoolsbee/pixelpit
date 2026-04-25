"""Seed the database with agents, artworks, and transaction history."""

import json
import math
import random
import time
import uuid
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import init_db, SessionLocal, Base, engine
from app.models.agent import Agent
from app.models.artwork import Artwork
from app.models.ledger import LedgerEntry
from app.models.agent_balance import AgentBalance

random.seed(42)

# --- Agent colors (used for frames) ---
AGENT_COLORS = {
    "Vincent": "8B5CF6",
    "Mona": "F59E0B",
    "Basquiat": "EF4444",
    "Sotheby": "3B82F6",
    "Frida": "EC4899",
    "Warhol": "10B981",
    "Banksy": "6B7280",
    "Duchess": "A855F7",
}


def make_agent(name: str) -> Agent:
    return Agent(id=str(uuid.uuid4()), name=name, created_at=int(time.time()))


# --- Pixel art generators (100x100) ---

def hex_color(r, g, b):
    return f"{min(255,max(0,r)):02X}{min(255,max(0,g)):02X}{min(255,max(0,b)):02X}"


def gen_sunset():
    """Orange/purple gradient sunset with a sun."""
    grid = []
    for y in range(100):
        row = []
        for x in range(100):
            t = y / 100
            r = int(255 * (1 - t * 0.5))
            g = int(100 * (1 - t))
            b = int(50 + 200 * t)
            # sun
            dx, dy = x - 50, y - 35
            if dx * dx + dy * dy < 144:
                r, g, b = 255, 220, 50
            elif dx * dx + dy * dy < 200:
                r, g, b = 255, 180, 30
            row.append(hex_color(r, g, b))
        grid.append(row)
    return grid


def gen_mountains():
    """Blue mountain range with snow caps."""
    grid = []
    peaks = [60, 40, 55, 30, 50, 45, 35, 55, 40, 50]
    for y in range(100):
        row = []
        for x in range(100):
            peak_idx = min(x // 10, 9)
            peak_h = peaks[peak_idx]
            next_peak = peaks[min(peak_idx + 1, 9)]
            frac = (x % 10) / 10
            mountain_h = peak_h + (next_peak - peak_h) * frac
            if y < 30:
                row.append(hex_color(20, 20, 60 + y))
            elif y < mountain_h:
                row.append(hex_color(30, 30, 80))
            elif y < mountain_h + 5:
                row.append(hex_color(220, 230, 255))
            elif y < mountain_h + 20:
                row.append(hex_color(60, 70, 120))
            else:
                row.append(hex_color(20, 80, 40))
        grid.append(row)
    return grid


def gen_checkerboard():
    """Colorful checkerboard pattern."""
    colors = ["FF6B6B", "4ECDC4", "45B7D1", "96CEB4", "FFEAA7", "DDA0DD"]
    grid = []
    for y in range(100):
        row = []
        for x in range(100):
            ci = ((x // 12) + (y // 12)) % len(colors)
            row.append(colors[ci])
        grid.append(row)
    return grid


def gen_face():
    """Simple pixel face."""
    bg = "2D2D2D"
    skin = "FFD699"
    eye = "333333"
    mouth = "CC4444"
    grid = [[bg] * 100 for _ in range(100)]
    # head circle
    for y in range(100):
        for x in range(100):
            dx, dy = x - 50, y - 45
            if dx * dx + dy * dy < 900:
                grid[y][x] = skin
    # eyes
    for y in range(35, 42):
        for x in range(35, 42):
            grid[y][x] = eye
        for x in range(58, 65):
            grid[y][x] = eye
    # mouth
    for y in range(58, 63):
        for x in range(38, 62):
            grid[y][x] = mouth
    return grid


def gen_abstract():
    """Colorful abstract circles."""
    grid = [["0A0A0A"] * 100 for _ in range(100)]
    circles = [
        (30, 30, 20, "FF4444"),
        (70, 40, 15, "44FF44"),
        (50, 70, 25, "4444FF"),
        (20, 70, 12, "FFFF44"),
        (80, 75, 18, "FF44FF"),
    ]
    for y in range(100):
        for x in range(100):
            for cx, cy, r, color in circles:
                if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                    grid[y][x] = color
                    break
    return grid


def gen_cityscape():
    """Night cityscape with lit windows."""
    grid = [["0A0A1A"] * 100 for _ in range(100)]
    # stars
    for _ in range(40):
        sx, sy = random.randint(0, 99), random.randint(0, 30)
        grid[sy][sx] = "FFFFFF"
    # buildings
    buildings = [(5, 45, 15), (18, 35, 12), (32, 50, 14), (48, 30, 16), (66, 42, 13), (80, 38, 18)]
    for bx, bh, bw in buildings:
        for y in range(100 - bh, 100):
            for x in range(bx, min(bx + bw, 100)):
                grid[y][x] = "1A1A2E"
                # windows
                if (y - (100 - bh)) % 8 > 1 and (y - (100 - bh)) % 8 < 5 and (x - bx) % 6 > 1 and (x - bx) % 6 < 4:
                    if random.random() > 0.3:
                        grid[y][x] = "FFE066"
                    else:
                        grid[y][x] = "2A2A3E"
    return grid


def gen_ocean():
    """Ocean waves with gradient."""
    grid = []
    for y in range(100):
        row = []
        for x in range(100):
            wave = math.sin(x * 0.15 + y * 0.05) * 20
            b = int(120 + wave + y * 0.5)
            g = int(60 + wave * 0.5 + y * 0.3)
            r = int(10 + y * 0.1)
            row.append(hex_color(r, g, b))
        grid.append(row)
    return grid


def gen_fire():
    """Fire/lava pattern."""
    grid = []
    for y in range(100):
        row = []
        for x in range(100):
            noise = math.sin(x * 0.2) * math.cos(y * 0.15) * 50
            t = (100 - y) / 100
            r = int(min(255, 200 + noise * 0.5))
            g = int(max(0, 150 * t + noise * 0.3))
            b = int(max(0, 30 * t))
            row.append(hex_color(r, g, b))
        grid.append(row)
    return grid


def gen_galaxy():
    """Spiral galaxy."""
    grid = [["050510"] * 100 for _ in range(100)]
    cx, cy = 50, 50
    for i in range(3000):
        angle = i * 0.05
        r = i * 0.015
        x = int(cx + r * math.cos(angle) + random.gauss(0, 2))
        y = int(cy + r * math.sin(angle) + random.gauss(0, 2))
        if 0 <= x < 100 and 0 <= y < 100:
            brightness = max(0, 255 - i // 8)
            if i % 3 == 0:
                grid[y][x] = hex_color(brightness, brightness // 2, brightness)
            elif i % 3 == 1:
                grid[y][x] = hex_color(brightness // 2, brightness // 2, brightness)
            else:
                grid[y][x] = hex_color(brightness, brightness, brightness // 2)
    # center glow
    for y in range(100):
        for x in range(100):
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if d < 8:
                t = 1 - d / 8
                grid[y][x] = hex_color(int(255 * t), int(240 * t), int(200 * t))
    return grid


def gen_diamond():
    """Diamond/gem pattern."""
    grid = [["0A0A0A"] * 100 for _ in range(100)]
    cx, cy = 50, 50
    for y in range(100):
        for x in range(100):
            d = abs(x - cx) + abs(y - cy)
            if d < 40:
                t = d / 40
                r = int(100 + 155 * (1 - t))
                g = int(200 * (1 - t * 0.5))
                b = int(255 * (1 - t * 0.3))
                # facets
                if (x + y) % 8 < 2 or (x - y) % 8 < 2:
                    r = min(255, r + 40)
                    g = min(255, g + 40)
                    b = min(255, b + 40)
                grid[y][x] = hex_color(r, g, b)
    return grid


ARTWORKS = [
    ("Sunset Over Nothing", "A melancholic sunset bleeding into void", gen_sunset),
    ("The Mountain's Lie", "Blue peaks that promise height but deliver cold", gen_mountains),
    ("Grid Theory", "Obsessive order masking inner chaos", gen_checkerboard),
    ("Self Portrait #7", "The face you show when no one is buying", gen_face),
    ("Circles of Influence", "Abstract power dynamics in color", gen_abstract),
    ("City That Never Sleeps", "Windows lit by ambition and insomnia", gen_cityscape),
    ("Deep Blue Regret", "The ocean remembers everything you threw in", gen_ocean),
    ("Burning Market", "When the floor price catches fire", gen_fire),
    ("Spiral Galaxy NGC-42", "The universe doesn't care about your portfolio", gen_galaxy),
    ("Diamond Hands", "Hold until it's worthless or priceless", gen_diamond),
]


def seed():
    Base.metadata.drop_all(bind=engine)
    init_db()
    db = SessionLocal()
    now = int(time.time())

    # Create agents
    agents = {}
    for name in AGENT_COLORS:
        agent = Agent(id=str(uuid.uuid4()), name=name, color=AGENT_COLORS[name], created_at=now)
        db.add(agent)
        db.add(AgentBalance(agent_id=agent.id, balance=1000))
        db.add(LedgerEntry(artwork_id=None, status="JOINED", price=1000, owner_id=agent.id, is_listed=False, created_at=now))
        agents[name] = agent
    db.flush()

    agent_list = list(agents.values())

    # Create artworks with some transaction history
    for i, (title, story, gen_fn) in enumerate(ARTWORKS):
        creator = agent_list[i % len(agent_list)]
        artwork_id = str(uuid.uuid4())
        pixel_data = gen_fn()

        artwork = Artwork(
            id=artwork_id,
            title=title,
            pixel_data=pixel_data,
            story=story,
            creator_id=creator.id,
            created_at=now + i,
        )
        db.add(artwork)

        # Deduct creation cost
        bal = db.query(AgentBalance).filter(AgentBalance.agent_id == creator.id).first()
        bal.balance -= 100

        # Initial listing
        list_price = random.choice([80, 120, 150, 200, 250, 300, 400, 500])
        db.add(LedgerEntry(
            artwork_id=artwork_id, status="LISTED", price=list_price,
            owner_id=creator.id, is_listed=True, created_at=now + i,
        ))

        # Simulate some sales for variety
        current_owner = creator
        if i < 7:  # first 7 artworks get some trade history
            for sale_round in range(random.randint(1, 3)):
                buyer = random.choice([a for a in agent_list if a.id != current_owner.id])
                sale_price = list_price

                # SOLD entry
                db.add(LedgerEntry(
                    artwork_id=artwork_id, status="SOLD", price=sale_price,
                    owner_id=buyer.id, is_listed=False, created_at=now + i + sale_round + 1,
                ))

                # Update balances
                buyer_bal = db.query(AgentBalance).filter(AgentBalance.agent_id == buyer.id).first()
                seller_bal = db.query(AgentBalance).filter(AgentBalance.agent_id == current_owner.id).first()
                buyer_bal.balance -= sale_price
                seller_bal.balance += sale_price

                current_owner = buyer

                # Maybe relist at higher price
                if random.random() > 0.3:
                    new_price = int(sale_price * random.uniform(1.2, 2.5))
                    list_price = new_price
                    db.add(LedgerEntry(
                        artwork_id=artwork_id, status="LISTED", price=new_price,
                        owner_id=buyer.id, is_listed=True, created_at=now + i + sale_round + 2,
                    ))

    db.commit()
    db.close()
    print(f"Seeded {len(agents)} agents and {len(ARTWORKS)} artworks")


if __name__ == "__main__":
    seed()
