#!/usr/bin/env python3
"""display.py – OLED system dashboard

Renders a compact, animated HUD on the 128×64 SSD1306 OLED similar to the
provided mock-up image:
    • three header icons (music, chat, wrench – placeholder glyphs)
    • battery level indicator in the upper-right corner
    • horizontal rule separator
    • three resource bars: NPU (dummy), CPU and RAM with live percentages

Requirements: Pillow, psutil  (install with `pip3 install pillow psutil`)

The script re-uses the `SSD1306` driver class from `test.py` in the same
folder.  Press Ctrl+C to exit; the display is cleared automatically.
"""

import os
import time
from pathlib import Path

import psutil
from PIL import Image, ImageDraw, ImageFont

# Import the already implemented driver
from test import SSD1306  # noqa: E402 – local import on purpose

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FONT_PATHS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Debian/Ubuntu
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",   # Alternative
)


def load_font(size: int) -> ImageFont.ImageFont:
    """Best-effort TTF font loader with bitmap fallback."""
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


FONT_SMALL = load_font(8)
# Larger font for header icons
ICON_FONT = load_font(12)
FONT_TINY = load_font(6)


def read_battery_percent() -> int:
    """Return battery percentage (0-100).  Fallback to 100%% on desktops."""
    bat_path = Path("/sys/class/power_supply")
    for item in bat_path.glob("BAT*/capacity"):
        try:
            return int(item.read_text().strip())
        except (ValueError, OSError):
            pass
    return 100  # assume fully powered if no battery


# ---------------------------------------------------------------------------
# Drawing routine
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 128, 64
BAR_LEFT = 34      # start x of filled bars
BAR_RIGHT = 96     # end x of filled bars (just before closing bracket)
BAR_HEIGHT = 7
BAR_SPACING = 14   # vertical spacing between bars


def draw_dashboard(npu_pct: int, cpu_pct: float, ram_pct: float, bat_pct: int) -> Image.Image:
    """Return a rendered PIL image for the current metrics."""
    img = Image.new("1", (WIDTH, HEIGHT), 0)
    d = ImageDraw.Draw(img)

    # Header icons (very simple glyphs) – enlarged
    d.text((2, 0), "♪", font=ICON_FONT, fill=1)      # music note
    d.text((18, 0), "*", font=ICON_FONT, fill=1)      # placeholder chat icon
    d.text((34, 0), "#", font=ICON_FONT, fill=1)      # placeholder wrench

    # Battery outline
    d.rectangle((104, 2, 122, 14), outline=1)  # body
    d.rectangle((122, 5, 124, 11), fill=1)      # terminal
    # Battery fill
    fill_w = max(0, int((bat_pct / 100) * (122 - 104 - 2)))
    if fill_w:
        d.rectangle((106, 4, 106 + fill_w, 12), fill=1)

    # Separator line
    d.line((0, 18, WIDTH - 1, 18), fill=1)

    # Resource bars
    metrics = [
        ("NPU", int(npu_pct)),
        ("CPU", int(cpu_pct)),
        ("RAM", int(ram_pct)),
    ]

    for idx, (name, pct) in enumerate(metrics):
        y = 22 + idx * BAR_SPACING
        # label
        d.text((2, y), name, font=FONT_SMALL, fill=1)
        # brackets
        d.text((BAR_LEFT - 6, y), "[", font=FONT_SMALL, fill=1)
        d.text((BAR_RIGHT, y), "]", font=FONT_SMALL, fill=1)
        # percentage text
        pct_text = f"{pct:>3d}%"
        d.text((BAR_RIGHT + 8, y), pct_text, font=FONT_SMALL, fill=1)
        # bar fill
        bar_len = int((pct / 100) * (BAR_RIGHT - BAR_LEFT))
        if bar_len:
            d.rectangle((BAR_LEFT, y, BAR_LEFT + bar_len, y + BAR_HEIGHT), fill=1)

    return img


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    print("Starting OLED dashboard – Ctrl+C to quit")
    oled = None
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        dummy_npu_val = 0  # simple animated value
        direction = 1
        while True:
            # Simple bounce animation for NPU bar to mimic load changes
            dummy_npu_val += 5 * direction
            if dummy_npu_val >= 100 or dummy_npu_val <= 0:
                direction *= -1
                dummy_npu_val += 5 * direction

            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            bat = read_battery_percent()

            frame = draw_dashboard(dummy_npu_val, cpu, ram, bat)
            oled.display_image(frame)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as exc:
        print(f"Error: {exc}")
        raise  # Re-raise after cleanup
    finally:
        print("Cleaning up display...")
        if oled is not None:
            try:
                # Create a black image to clear the display
                clear_img = Image.new("1", (WIDTH, HEIGHT), 0)
                oled.display_image(clear_img)
                oled.clear()
                oled.close()
            except Exception as e:
                print(f"Warning: Error during cleanup: {e}")
        print("Done.")


if __name__ == "__main__":
    main()