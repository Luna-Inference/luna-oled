#!/usr/bin/env python3
"""display.py – OLED system dashboard

Renders a compact, animated HUD on the 128×64 SSD1306 OLED similar to the
provided mock-up image:
    • three header icons (music, chat, wrench – placeholder glyphs)
    • battery level indicator in the upper-right corner
    • horizontal rule separator
    • three resource bars: NPU, CPU and RAM with live percentages

Requirements: Pillow, requests (install with `pip3 install pillow requests`)

The script re-uses the `SSD1306` driver class from `test.py` in the same
folder.  Press Ctrl+C to exit; the display is cleared automatically.
"""

import json
import time
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageFont

# Import the already implemented driver
from test import SSD1306  # noqa: E402 – local import on purpose

# API Configuration
API_BASE_URL = "http://localhost:1309"
API_TIMEOUT = 2  # seconds

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


def fetch_metric(endpoint: str) -> float:
    """Fetch a metric from the API endpoint.
    
    Args:
        endpoint: The API endpoint to fetch from ('cpu', 'npu', or 'ram')
        
    Returns:
        float: The metric value as a percentage (0-100)
    """
    url = f"{API_BASE_URL}/{endpoint}"
    
    try:
        # Log the request for debugging
        print(f"Fetching {endpoint} from {url}...")
        
        # Make the request with a timeout
        response = requests.get(url, timeout=API_TIMEOUT)
        
        # Log the HTTP status code
        print(f"  Status code: {response.status_code}")
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Try to parse the JSON response
        try:
            data = response.json()
            print(f"  Response: {data}")
        except json.JSONDecodeError as e:
            print(f"  Error parsing JSON: {e}")
            print(f"  Response content: {response.text[:200]}")  # Show first 200 chars of response
            return 0
            
        # Extract the metric based on endpoint
        if endpoint == 'npu':
            # Try to get the average, fall back to calculating from cores if needed
            avg = data.get('npu_average_usage_percent')
            if avg is not None:
                return float(avg)
                
            # Fallback: Calculate average from cores if average not provided
            cores = data.get('npu_cores_usage_percent')
            if isinstance(cores, (list, tuple)) and len(cores) > 0:
                return sum(float(core) for core in cores) / len(cores)
            return 0
            
        elif endpoint == 'cpu':
            return float(data.get('cpu_usage_percent', 0))
            
        elif endpoint == 'ram':
            return float(data.get('ram_usage_percent', 0))
            
        return 0
        
    except requests.exceptions.HTTPError as e:
        print(f"  HTTP Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response content: {e.response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"  Request failed: {e}")
    except ValueError as e:
        print(f"  Value error: {e}")
    except Exception as e:
        print(f"  Unexpected error: {e}")
        
    # Return 0 as a fallback
    print(f"  Using fallback value: 0%")
    return 0


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


def draw_dashboard(npu_pct: float, cpu_pct: float, ram_pct: float, bat_pct: int) -> Image.Image:
    """Return a rendered PIL image for the current metrics.
    
    Args:
        npu_pct: NPU usage percentage (0-100)
        cpu_pct: CPU usage percentage (0-100)
        ram_pct: RAM usage percentage (0-100)
        bat_pct: Battery percentage (0-100)
    """
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
        pct_text = f"{min(100, max(0, pct)):>3d}%"  # Ensure 0-100 range
        d.text((BAR_RIGHT + 8, y), pct_text, font=FONT_SMALL, fill=1)
        # bar fill (clipped to 100%)
        bar_len = int((min(100, pct) / 100) * (BAR_RIGHT - BAR_LEFT))
        if bar_len > 0:
            d.rectangle((BAR_LEFT, y, BAR_LEFT + bar_len, y + BAR_HEIGHT), fill=1)

    return img


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    print("Starting OLED dashboard – Ctrl+C to quit")
    print(f"Fetching metrics from {API_BASE_URL}")
    
    oled = None
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
        while True:
            # Fetch metrics from API endpoints
            cpu = fetch_metric('cpu')
            npu = fetch_metric('npu')
            ram = fetch_metric('ram')
            bat = read_battery_percent()
            
            # Update display
            frame = draw_dashboard(npu, cpu, ram, bat)
            oled.display_image(frame)
            
            # Wait for next update (1 second)
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nDashboard stopped by user")
    except Exception as exc:
        print(f"Error: {exc}")
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