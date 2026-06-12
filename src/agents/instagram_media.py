"""
Instagram Media Pipeline
Generates images for Instagram posts using Pillow (no API key needed).
Creates branded graphics with text overlays.

Usage:
    python instagram_media.py --text "Your post text" --output output/ig_post.png
    python instagram_media.py --auto  # Generate for all scheduled posts
"""
import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont
import textwrap
import random

# Brand colors
BRAND_COLORS = {
    "dark": "#0a0a0a",
    "accent": "#6366f1",  # Indigo
    "accent_light": "#818cf8",
    "white": "#ffffff",
    "gray": "#9ca3af",
    "gradient_start": "#1e1b4b",
    "gradient_end": "#312e81",
}

TEMPLATES = [
    "dark_gradient",
    "accent_card",
    "minimal_dark",
    "quote_card",
    "stats_card",
]


def create_gradient(width, height, color1, color2):
    """Create a vertical gradient image."""
    base = Image.new("RGB", (width, height), color1)
    top = Image.new("RGB", (width, height), color2)
    mask = Image.new("L", (width, height))
    mask_data = []
    for y in range(height):
        for x in range(width):
            mask_data.append(int(255 * (y / height)))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base


def get_font(size=40, bold=False):
    """Get a font, falling back to default if custom font not available."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/c/Windows/Fonts/arialbd.ttf" if bold else "/c/Windows/Fonts/arial.ttf",
        "/c/Windows/Fonts/segoeuib.ttf" if bold else "/c/Windows/Fonts/segoeui.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()


def generate_image(text: str, output_path: str, template: str = "dark_gradient",
                   width: int = 1080, height: int = 1080) -> str:
    """Generate an Instagram-ready image with text overlay."""

    # Create background
    if template == "dark_gradient":
        img = create_gradient(width, height, BRAND_COLORS["gradient_start"], BRAND_COLORS["gradient_end"])
    elif template == "accent_card":
        img = Image.new("RGB", (width, height), BRAND_COLORS["dark"])
        draw = ImageDraw.Draw(img)
        # Accent bar at top
        draw.rectangle([0, 0, width, 8], fill=BRAND_COLORS["accent"])
        # Accent card in center
        margin = 80
        draw.rectangle([margin, margin, width-margin, height-margin],
                       fill="#1a1a2e", outline=BRAND_COLORS["accent"], width=3)
    elif template == "minimal_dark":
        img = Image.new("RGB", (width, height), BRAND_COLORS["dark"])
    elif template == "quote_card":
        img = create_gradient(width, height, "#0f0f23", "#1a1a3e")
    elif template == "stats_card":
        img = Image.new("RGB", (width, height), BRAND_COLORS["dark"])
    else:
        img = create_gradient(width, height, BRAND_COLORS["gradient_start"], BRAND_COLORS["gradient_end"])

    draw = ImageDraw.Draw(img)

    # Add brand watermark
    brand_font = get_font(size=24)
    draw.text((width - 200, height - 50), "AgentsFactory", fill=BRAND_COLORS["gray"], font=brand_font)

    # Add main text
    main_font = get_font(size=48, bold=True)
    sub_font = get_font(size=32)

    # Wrap text
    lines = textwrap.wrap(text, width=35)
    if not lines:
        lines = [text]

    # Calculate text position (centered)
    line_height = 60
    total_height = len(lines) * line_height
    y_start = (height - total_height) // 2

    for i, line in enumerate(lines):
        # Get text width for centering
        bbox = draw.textbbox((0, 0), line, font=main_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = y_start + i * line_height

        # Draw text with slight shadow
        draw.text((x+2, y+2), line, fill="#000000", font=main_font)
        draw.text((x, y), line, fill=BRAND_COLORS["white"], font=main_font)

    # Add accent line
    line_y = y_start + total_height + 40
    draw.line([(width//2 - 100, line_y), (width//2 + 100, line_y)],
              fill=BRAND_COLORS["accent"], width=3)

    # Save
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    return output_path


def generate_instagram_post(text: str, output_dir: str = "output/instagram") -> dict:
    """Generate a complete Instagram post with image and caption."""
    os.makedirs(output_dir, exist_ok=True)

    timestamp = random.randint(1000, 9999)
    template = random.choice(TEMPLATES)
    image_path = f"{output_dir}/ig_post_{timestamp}.png"

    # Generate image
    generate_image(text[:200], image_path, template=template)

    # Generate caption (longer, with hashtags)
    caption = f"{text}\n.\n.\n.\n#AIAgents #Automation #BuildingInPublic #SaaS #Ecommerce #StartupLife #TechStartup #Entrepreneurship #DigitalMarketing"

    return {
        "image_path": image_path,
        "caption": caption,
        "template": template,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram Media Pipeline")
    parser.add_argument("--text", type=str, default="AI automation saves 20+ hours/week", help="Text for the image")
    parser.add_argument("--output", type=str, default="output/ig_post.png", help="Output path")
    parser.add_argument("--template", type=str, default="dark_gradient", choices=TEMPLATES)
    parser.add_argument("--auto", action="store_true", help="Generate for all scheduled posts")
    args = parser.parse_args()

    if args.auto:
        print("Auto-generating Instagram posts for scheduled content...")
    else:
        result = generate_instagram_post(args.text)
        print(f"✅ Image saved: {result['image_path']}")
        print(f"   Caption: {result['caption'][:80]}...")
