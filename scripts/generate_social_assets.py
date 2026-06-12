"""
Generate branded Instagram post images for AgentsFactory.
Saves 10 square (1080x1080) PNG images to docs/landing/social-assets/.
"""
from PIL import Image, ImageDraw, ImageFont
import os
import math

# ── Brand colours ──────────────────────────────────────────────
BG          = (10, 10, 10)          # #0a0a0a
ACCENT      = (99, 102, 241)        # #6366f1
ACCENT_LIGHT= (129, 140, 248)       # #818cf8
WHITE       = (255, 255, 255)
DARK_TEXT   = (30, 30, 40)
GREY        = (160, 160, 170)
MID_GREY    = (80, 80, 90)
CARD_BG     = (20, 20, 28)
GOLD        = (251, 191, 36)
GREEN       = (52, 211, 153)
RED         = (248, 113, 113)
BLUE        = (96, 165, 250)
PURPLE      = (167, 139, 250)
TEAL        = (45, 212, 191)

SIZE = 1080
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "landing", "social-assets")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Fonts ───────────────────────────────────────────────────────
FONTS = {
    "regular":  "C:/Windows/Fonts/arial.ttf",
    "bold":     "C:/Windows/Fonts/arialbd.ttf",
    "italic":   "C:/Windows/Fonts/ariali.ttf",
    "segoe":    "C:/Windows/Fonts/segoeui.ttf",
    "segoeb":   "C:/Windows/Fonts/segoeuib.ttf",
    "segoel":   "C:/Windows/Fonts/segoeuil.ttf",
}

def font(name, size):
    try:
        return ImageFont.truetype(FONTS[name], size)
    except Exception:
        return ImageFont.load_default()

def center_text(draw, y, text, fnt, fill, width=SIZE):
    """Draw horizontally centred text."""
    bbox = draw.textbbox((0, 0), text, font=fnt)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=fnt, fill=fill)
    return bbox[3] - bbox[1]  # height used

def rounded_rect(draw, xy, radius, fill, outline=None, outline_width=2):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill,
                            outline=outline or fill, width=outline_width)

def gradient_bg(img, color_top, color_bottom):
    """Vertical gradient background."""
    draw = ImageDraw.Draw(img)
    for y in range(SIZE):
        t = y / SIZE
        r = int(color_top[0] * (1 - t) + color_bottom[0] * t)
        g = int(color_top[1] * (1 - t) + color_bottom[1] * t)
        b = int(color_top[2] * (1 - t) + color_bottom[2] * t)
        draw.line([(0, y), (SIZE, y)], fill=(r, g, b))

def add_bottom_bar(draw):
    """Thin accent bar at the bottom."""
    draw.rectangle([0, SIZE - 6, SIZE, SIZE], fill=ACCENT)

def add_logo_watermark(draw, x, y):
    """Small AgentsFactory watermark."""
    fnt = font("segoel", 18)
    draw.text((x, y), "AgentsFactory", font=fnt, fill=(60, 60, 75))

def add_deco_circles(draw):
    """Subtle decorative circles in background."""
    draw.ellipse([700, -80, 1180, 400], fill=(15, 15, 30))
    draw.ellipse([-100, 600, 300, 1000], fill=(15, 15, 30))
    draw.ellipse([800, 750, 1050, 1000], fill=(20, 15, 40))

# ── Image 1: Brand / Welcome ──────────────────────────────────
def make_brand_welcome():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (10, 10, 18), (15, 10, 30))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    # Big accent circle behind logo area
    draw.ellipse([390, 180, 690, 480], fill=ACCENT)
    draw.ellipse([410, 200, 670, 460], fill=BG)

    # "AF" monogram
    fnt_mono = font("segoeb", 140)
    center_text(draw, 250, "AF", fnt_mono, ACCENT)

    # Brand name
    fnt_title = font("segoeb", 58)
    center_text(draw, 520, "AgentsFactory", fnt_title, WHITE)

    # Tagline
    fnt_tag = font("regular", 28)
    center_text(draw, 610, "AI Automation Agency", fnt_tag, ACCENT_LIGHT)

    # Divider
    draw.rectangle([340, 665, 740, 669], fill=ACCENT)

    # Sub-text
    fnt_sub = font("regular", 22)
    center_text(draw, 690, "Helping businesses automate", fnt_sub, GREY)
    center_text(draw, 725, "with intelligent AI agents", fnt_sub, GREY)

    # Website
    fnt_url = font("segoel", 20)
    center_text(draw, 800, "agentsfactory.com", fnt_url, MID_GREY)

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "01_brand_welcome.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 2: Day X Progress ────────────────────────────────────
def make_day_progress(day=1):
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (10, 10, 16), (12, 8, 28))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    # Day badge
    rounded_rect(draw, [340, 100, 740, 220], 20, ACCENT)
    fnt_day_lbl = font("regular", 22)
    center_text(draw, 115, "DAY", fnt_day_lbl, WHITE)
    fnt_day_num = font("segoeb", 72)
    center_text(draw, 142, str(day), fnt_day_num, WHITE)

    # Title
    fnt_title = font("segoeb", 44)
    center_text(draw, 260, "Building AgentsFactory", fnt_title, WHITE)

    # Progress bar
    bar_x0, bar_x1 = 140, 940
    bar_y = 340
    progress = min(day / 30, 1.0)
    draw.rounded_rectangle([bar_x0, bar_y, bar_x1, bar_y + 20], radius=10, fill=MID_GREY)
    if progress > 0:
        draw.rounded_rectangle([bar_x0, bar_y, bar_x0 + int(800 * progress), bar_y + 20],
                                radius=10, fill=ACCENT)
    fnt_pct = font("regular", 18)
    center_text(draw, bar_y + 30, f"{int(progress * 100)}% Complete", fnt_pct, GREY)

    # Milestones
    milestones = [
        ("✅", "8 AI Subagents", True),
        ("✅", "Lead Finder Agent", True),
        ("✅", "Content Writer", True),
        ("✅", "LinkedIn Agent", True),
        ("🔄", "Outreach Agent", day >= 10),
        ("⬜", "Analytics Dashboard", day >= 15),
        ("⬜", "Client Portal", day >= 20),
        ("⬜", "Full Automation", day >= 30),
    ]
    fnt_ms = font("regular", 24)
    y = 420
    for icon, label, done in milestones:
        color = GREEN if done else GREY
        draw.text((180, y), icon, font=fnt_ms, fill=color)
        draw.text((230, y), label, font=fnt_ms, fill=color if done else MID_GREY)
        y += 45

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "02_day_progress.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 3: AI Agent Explainer ────────────────────────────────
def make_ai_agent_explainer():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (8, 8, 18), (12, 10, 35))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    fnt_title = font("segoeb", 52)
    center_text(draw, 50, "What is an", fnt_title, WHITE)
    fnt_title2 = font("segoeb", 62)
    center_text(draw, 115, "AI Agent?", fnt_title2, ACCENT)

    # Divider
    draw.rectangle([340, 200, 740, 204], fill=ACCENT)

    # Definition box
    rounded_rect(draw, [100, 230, 980, 380], 16, CARD_BG, outline=ACCENT)
    fnt_def = font("regular", 24)
    lines = [
        "An AI agent is a software system that",
        "perceives its environment, makes decisions,",
        "and takes actions to achieve goals —",
        "autonomously.",
    ]
    y = 255
    for line in lines:
        center_text(draw, y, line, fnt_def, WHITE)
        y += 36

    # Agent types
    agents = [
        ("🔍", "Research", "Scans & analyzes data"),
        ("✍️", "Writing", "Creates content & copy"),
        ("📊", "Analytics", "Tracks & reports metrics"),
        ("🤝", "Engagement", "Nurtures leads 24/7"),
        ("⚡", "Automation", "Connects your tools"),
    ]
    fnt_aname = font("bold", 26)
    fnt_adesc = font("regular", 18)
    y = 410
    for icon, name, desc in agents:
        draw.text((140, y), icon, font=fnt_aname, fill=WHITE)
        draw.text((195, y + 2), name, font=fnt_aname, fill=ACCENT_LIGHT)
        draw.text((195, y + 32), desc, font=fnt_adesc, fill=GREY)
        y += 75

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "03_ai_agent_explainer.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 4: Services Overview ─────────────────────────────────
def make_services_overview():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (10, 10, 20), (15, 10, 30))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    fnt_title = font("segoeb", 52)
    center_text(draw, 40, "Our Services", fnt_title, WHITE)

    draw.rectangle([340, 115, 740, 119], fill=ACCENT)

    plans = [
        ("STARTER", "$500/mo", GREEN, [
            "2 AI Agents",
            "Basic Automation",
            "Weekly Reports",
            "Email Support",
        ]),
        ("GROWTH", "$1,500/mo", ACCENT, [
            "5 AI Agents",
            "Full Automation",
            "Daily Reports",
            "Priority Support",
            "Custom Workflows",
        ]),
        ("SCALE", "$3,000/mo", GOLD, [
            "Unlimited Agents",
            "Enterprise Automation",
            "Real-time Dashboard",
            "Dedicated Manager",
            "Custom Integrations",
            "SLA Guarantee",
        ]),
    ]

    card_width = 300
    gap = 20
    total_w = len(plans) * card_width + (len(plans) - 1) * gap
    start_x = (SIZE - total_w) // 2

    for i, (name, price, color, features) in enumerate(plans):
        x0 = start_x + i * (card_width + gap)
        y0 = 150
        card_h = 750

        # Card background
        rounded_rect(draw, [x0, y0, x0 + card_width, y0 + card_h], 16,
                     CARD_BG, outline=color)

        # Plan name
        fnt_pname = font("segoeb", 28)
        center_text(draw, y0 + 25, name, fnt_pname, color, width=x0 + card_width)
        # Adjust x for center_text
        bbox = draw.textbbox((0, 0), name, font=fnt_pname)
        tw = bbox[2] - bbox[0]
        draw.text((x0 + (card_width - tw) // 2, y0 + 25), name, font=fnt_pname, fill=color)

        # Price
        fnt_price = font("segoeb", 38)
        bbox = draw.textbbox((0, 0), price, font=fnt_price)
        tw = bbox[2] - bbox[0]
        draw.text((x0 + (card_width - tw) // 2, y0 + 70), price, font=fnt_price, fill=WHITE)

        # Divider
        draw.rectangle([x0 + 30, y0 + 130, x0 + card_width - 30, y0 + 133], fill=color)

        # Features
        fnt_feat = font("regular", 20)
        fy = y0 + 155
        for feat in features:
            txt = f"✓  {feat}"
            bbox = draw.textbbox((0, 0), txt, font=fnt_feat)
            tw = bbox[2] - bbox[0]
            draw.text((x0 + (card_width - tw) // 2, fy), txt, font=fnt_feat, fill=GREY)
            fy += 38

        # CTA button
        btn_y = y0 + card_h - 70
        rounded_rect(draw, [x0 + 40, btn_y, x0 + card_width - 40, btn_y + 48], 10, color)
        fnt_cta = font("bold", 20)
        bbox = draw.textbbox((0, 0), "Get Started", font=fnt_cta)
        tw = bbox[2] - bbox[0]
        draw.text((x0 + (card_width - tw) // 2, btn_y + 12), "Get Started", font=fnt_cta, fill=WHITE)

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "04_services_overview.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 5: What Are AI Agents (Educational) ──────────────────
def make_what_are_agents():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (8, 8, 16), (10, 8, 28))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    fnt_title = font("segoeb", 48)
    center_text(draw, 40, "What Are", fnt_title, WHITE)
    fnt_title2 = font("segoeb", 62)
    center_text(draw, 100, "AI Agents?", fnt_title2, ACCENT)

    draw.rectangle([300, 185, 780, 189], fill=ACCENT)

    # Central brain/agent graphic
    cx, cy = 540, 420
    for r in range(120, 0, -20):
        alpha = int(40 + (120 - r) * 1.2)
        color = (ACCENT[0], ACCENT[1], min(255, ACCENT[2] + 40))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(color[0]//4, color[1]//4, min(255, color[2]//3)))

    draw.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=ACCENT)
    fnt_bot = font("segoeb", 40)
    bbox = draw.textbbox((0, 0), "🤖", font=fnt_bot)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2), "🤖", font=fnt_bot, fill=WHITE)

    # Orbiting labels
    labels = [
        (cx, cy - 100, "Perceive"),
        (cx + 100, cy - 30, "Decide"),
        (cx + 80, cy + 80, "Act"),
        (cx - 80, cy + 80, "Learn"),
        (cx - 100, cy - 30, "Adapt"),
    ]
    fnt_lbl = font("bold", 22)
    for lx, ly, txt in labels:
        bbox = draw.textbbox((0, 0), txt, font=fnt_lbl)
        tw = bbox[2] - bbox[0]
        draw.text((lx - tw // 2, ly), txt, font=fnt_lbl, fill=ACCENT_LIGHT)

    # Bottom text
    fnt_sub = font("regular", 24)
    center_text(draw, 600, "AI Agents perceive, decide, act,", fnt_sub, WHITE)
    center_text(draw, 635, "learn, and adapt — autonomously.", fnt_sub, WHITE)

    # Key point box
    rounded_rect(draw, [140, 700, 940, 830], 16, CARD_BG, outline=ACCENT)
    fnt_key = font("bold", 26)
    center_text(draw, 720, "Key Insight", fnt_key, ACCENT)
    fnt_val = font("regular", 22)
    center_text(draw, 760, "They don't just respond — they take", fnt_val, WHITE)
    center_text(draw, 790, "initiative to achieve your goals.", fnt_val, WHITE)

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "05_what_are_agents.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 6: Behind the Scenes ─────────────────────────────────
def make_behind_scenes():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (10, 10, 18), (18, 10, 25))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    # Header badge
    rounded_rect(draw, [290, 40, 790, 90], 12, ACCENT)
    fnt_badge = font("bold", 24)
    center_text(draw, 52, "🔧 BEHIND THE SCENES", fnt_badge, WHITE)

    fnt_title = font("segoeb", 46)
    center_text(draw, 120, "Building in Public", fnt_title, WHITE)

    draw.rectangle([340, 190, 740, 194], fill=ACCENT)

    # Timeline items
    timeline = [
        ("Week 1", "Ideation & Research", "Defined the problem space\nand identified target clients", True),
        ("Week 2", "Agent Architecture", "Designed 8 specialized AI agents\nwith clear responsibilities", True),
        ("Week 3", "Content Engine", "Built automated content pipeline\nfor all social platforms", True),
        ("Week 4", "Outreach System", "Automated lead generation\nand DM outreach system", True),
        ("Week 5", "Dashboard & Analytics", "Real-time command center\ntracking all operations", False),
        ("Week 6", "Client Onboarding", "Streamlined onboarding\nand delivery process", False),
    ]

    fnt_week = font("bold", 22)
    fnt_phase = font("bold", 24)
    fnt_desc = font("regular", 18)

    y = 220
    for week, phase, desc, done in timeline:
        color = GREEN if done else MID_GREY
        # Week label
        draw.text((100, y), week, font=fnt_week, fill=color)
        # Phase name
        draw.text((230, y), phase, font=fnt_phase, fill=WHITE if done else GREY)
        # Description lines
        for di, dline in enumerate(desc.split('\n')):
            draw.text((230, y + 30 + di * 24), dline, font=fnt_desc, fill=MID_GREY)
        # Status icon
        icon = "✅" if done else "⬜"
        draw.text([880, y], icon, font=fnt_week, fill=color)
        y += 90

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "06_behind_scenes.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 7: Client Results / Testimonial ──────────────────────
def make_testimonial():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (10, 10, 18), (15, 12, 28))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    fnt_title = font("segoeb", 48)
    center_text(draw, 50, "Client Results", fnt_title, WHITE)

    draw.rectangle([340, 125, 740, 129], fill=ACCENT)

    # Quote box
    rounded_rect(draw, [100, 160, 980, 420], 20, CARD_BG, outline=ACCENT)

    # Quote marks
    fnt_quote_mark = font("segoeb", 100)
    draw.text((120, 155), '\u201c\u201c', font=fnt_quote_mark, fill=ACCENT)

    fnt_quote = font("italic", 28)
    quote_lines = [
        "AgentsFactory automated our entire",
        "lead gen pipeline. We went from 5",
        "to 50 qualified leads per week.",
    ]
    y = 200
    for line in quote_lines:
        center_text(draw, y, line, fnt_quote, WHITE)
        y += 40

    # Attribution
    fnt_attr = font("bold", 24)
    center_text(draw, 350, "— Sarah Chen, CEO", fnt_attr, ACCENT_LIGHT)
    fnt_attr2 = font("regular", 20)
    center_text(draw, 385, "TechStart Inc.", fnt_attr2, GREY)

    # Stats row
    stats = [
        ("3x", "More Leads"),
        ("80%", "Time Saved"),
        ("$12K", "Revenue Added"),
    ]
    stat_xs = [180, 440, 700]
    fnt_num = font("segoeb", 52)
    fnt_lbl = font("regular", 20)
    for i, (num, lbl) in enumerate(stats):
        sx = stat_xs[i]
        # Stat card
        rounded_rect(draw, [sx - 40, 470, sx + 160, 620], 16, CARD_BG)
        bbox = draw.textbbox((0, 0), num, font=fnt_num)
        tw = bbox[2] - bbox[0]
        draw.text((sx + (120 - tw) // 2 - 10, 485), num, font=fnt_num, fill=ACCENT)
        bbox2 = draw.textbbox((0, 0), lbl, font=fnt_lbl)
        tw2 = bbox2[2] - bbox2[0]
        draw.text((sx + (120 - tw2) // 2 - 10, 555), lbl, font=fnt_lbl, fill=GREY)

    # CTA
    rounded_rect(draw, [240, 670, 840, 740], 14, ACCENT)
    fnt_cta = font("bold", 28)
    center_text(draw, 685, "Want Similar Results?  →  DM Us", fnt_cta, WHITE)

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "07_testimonial.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 8: 5 Things I Learned ────────────────────────────────
def make_5_things_learned():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (8, 8, 18), (12, 10, 30))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    fnt_title = font("segoeb", 44)
    center_text(draw, 35, "5 Things I Learned", fnt_title, WHITE)
    fnt_sub = font("segoeb", 36)
    center_text(draw, 90, "Building an AI Agency", fnt_sub, ACCENT)

    draw.rectangle([300, 150, 780, 154], fill=ACCENT)

    items = [
        ("1", "Start with ONE Agent",
         "Get it working perfectly\nbefore adding another"),
        ("2", "Content is King",
         "Post daily. Be consistent.\nIt's the best lead gen tool"),
        ("3", "Automation Compounds",
         "Each agent makes the next\none easier to build"),
        ("4", "Free Models Work",
         "Don't pay for AI until\nyou're ready to scale"),
        ("5", "Decide Faster",
         "The bottleneck is always\ndecision-making, not execution"),
    ]

    fnt_num = font("segoeb", 42)
    fnt_itle = font("bold", 24)
    fnt_desc = font("regular", 19)

    y = 175
    for num, title, desc in items:
        # Number circle
        draw.ellipse([80, y + 5, 130, y + 55], fill=ACCENT)
        bbox = draw.textbbox((0, 0), num, font=fnt_num)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((105 - tw // 2, y + 12 - th // 2), num, font=fnt_num, fill=WHITE)

        # Title
        draw.text((155, y + 2), title, font=fnt_itle, fill=WHITE)

        # Description
        for di, dline in enumerate(desc.split('\n')):
            draw.text((155, y + 35 + di * 26), dline, font=fnt_desc, fill=GREY)

        y += 105

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "08_five_things_learned.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 9: Automation Workflow ───────────────────────────────
def make_workflow_diagram():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (8, 8, 16), (10, 8, 28))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    fnt_title = font("segoeb", 46)
    center_text(draw, 35, "Automation Workflow", fnt_title, WHITE)

    draw.rectangle([300, 105, 780, 109], fill=ACCENT)

    # Workflow steps (vertical flow)
    steps = [
        ("📥", "Input", "Client data, leads,\ncontent ideas", ACCENT),
        ("🔍", "Research Agent", "Scans 100+ prospects\nin minutes", BLUE),
        ("✍️", "Content Agent", "Drafts posts, emails,\nreports automatically", PURPLE),
        ("🤝", "Engagement Agent", "Nurtures leads\n24/7 across platforms", TEAL),
        ("📊", "Analytics Agent", "Tracks metrics &\noptimizes performance", GOLD),
        ("📤", "Output", "Qualified leads,\ncontent, reports", GREEN),
    ]

    box_w, box_h = 380, 80
    x0 = (SIZE - box_w) // 2
    y_start = 130
    gap = 100

    for i, (icon, name, desc, color) in enumerate(steps):
        y = y_start + i * gap

        # Box
        rounded_rect(draw, [x0, y, x0 + box_w, y + box_h], 14, CARD_BG, outline=color)

        # Icon
        fnt_icon = font("segoeb", 32)
        draw.text((x0 + 20, y + 20), icon, font=fnt_icon, fill=color)

        # Name
        fnt_name = font("bold", 22)
        draw.text((x0 + 75, y + 12), name, font=fnt_name, fill=color)

        # Description
        fnt_desc = font("regular", 17)
        for di, dline in enumerate(desc.split('\n')):
            draw.text((x0 + 75, y + 40 + di * 22), dline, font=fnt_desc, fill=GREY)

        # Arrow to next
        if i < len(steps) - 1:
            arrow_y = y + box_h + 10
            ax = SIZE // 2
            draw.polygon([(ax - 12, arrow_y), (ax + 12, arrow_y), (ax, arrow_y + 14)], fill=MID_GREY)

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "09_workflow_diagram.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path

# ── Image 10: Call to Action / DM Me ───────────────────────────
def make_cta():
    img = Image.new("RGB", (SIZE, SIZE), BG)
    gradient_bg(img, (10, 10, 20), (20, 10, 40))
    draw = ImageDraw.Draw(img)
    add_deco_circles(draw)

    # Large accent circle glow
    for r in range(250, 0, -10):
        t = r / 250
        c = (int(ACCENT[0] * (1 - t) * 0.3), int(ACCENT[1] * (1 - t) * 0.3), int(ACCENT[2] * (1 - t) * 0.5))
        draw.ellipse([540 - r, 350 - r, 540 + r, 350 + r], fill=c)

    # Main CTA circle
    draw.ellipse([340, 150, 740, 550], fill=ACCENT)
    draw.ellipse([360, 170, 720, 530], fill=BG)

    fnt_big = font("segoeb", 72)
    center_text(draw, 240, "DM", fnt_big, ACCENT)

    fnt_us = font("segoeb", 36)
    center_text(draw, 340, "US", fnt_us, WHITE)

    fnt_arrow = font("segoeb", 40)
    center_text(draw, 400, "↓", fnt_arrow, ACCENT_LIGHT)

    # Message
    fnt_msg = font("bold", 30)
    center_text(draw, 580, "Want to automate", fnt_msg, WHITE)
    center_text(draw, 620, "your business?", fnt_msg, WHITE)

    # Sub
    fnt_sub = font("regular", 24)
    center_text(draw, 680, "Drop us a DM and let's talk", fnt_sub, GREY)
    center_text(draw, 715, "about your automation needs", fnt_sub, GREY)

    # Contact box
    rounded_rect(draw, [240, 780, 840, 860], 14, CARD_BG, outline=ACCENT)
    fnt_cta = font("bold", 26)
    center_text(draw, 795, "📩  hello@agentsfactory.com", fnt_cta, WHITE)

    add_bottom_bar(draw)
    add_logo_watermark(draw, 40, SIZE - 35)

    path = os.path.join(OUTPUT_DIR, "10_cta_dm.png")
    img.save(path, "PNG")
    print(f"✅ Saved: {path}")
    return path


# ── Main ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🎨 Generating AgentsFactory Instagram assets...\n")
    paths = []
    paths.append(make_brand_welcome())
    paths.append(make_day_progress(day=1))
    paths.append(make_ai_agent_explainer())
    paths.append(make_services_overview())
    paths.append(make_what_are_agents())
    paths.append(make_behind_scenes())
    paths.append(make_testimonial())
    paths.append(make_5_things_learned())
    paths.append(make_workflow_diagram())
    paths.append(make_cta())
    print(f"\n✅ All {len(paths)} images generated in: {OUTPUT_DIR}")
