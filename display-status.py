#!/usr/bin/env python3
"""display-status.py – OLED LLM Status Indicator

Displays status of the LLM service and generation state using icons.
- Green circle: Service running
- Red X: Service not running
- Dot: Generating
- No dot: Idle
"""

import time
import signal
import sys
import requests
from PIL import Image, ImageDraw

# Import the display driver
from test import SSD1306  # noqa: E402 – local import on purpose

# API Configuration
LLM_HEALTH_URL = "http://localhost:1306/health"
API_TIMEOUT = 2  # seconds

# Display Configuration
WIDTH, HEIGHT = 128, 64

# Global OLED instance for cleanup
oled = None


def cleanup():
    """Clean up the display and exit."""
    global oled
    print("\nCleaning up display...")
    if oled is not None:
        try:
            # Create a blank black image
            clear_img = Image.new("1", (WIDTH, HEIGHT), 0)
            # Display the blank image
            oled.display_image(clear_img)
            # Clear the display buffer
            oled.clear()
            # Close the display
            oled.close()
            print("Display cleared successfully.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            oled = None
    sys.exit(0)


def signal_handler(sig, frame):
    """Handle interrupt signals."""
    print("\nReceived interrupt signal")
    cleanup()


def get_llm_status():
    """Get LLM status including generation state."""
    try:
        response = requests.get(LLM_HEALTH_URL, timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            return {
                'running': data.get('status') == 'healthy',
                'generating': not data.get('generation_status') == 'idle'
            }
    except (requests.RequestException, ValueError):
        pass
    return {'running': False, 'generating': False}


def draw_status_icon(running: bool, generating: bool) -> Image.Image:
    """Draw status icons based on LLM state."""
    img = Image.new("1", (WIDTH, HEIGHT), 0)  # 1-bit image (black background)
    d = ImageDraw.Draw(img)
    
    # Position for the status icon
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    radius = min(WIDTH, HEIGHT) // 4  # Smaller radius since we'll have two states
    
    # Draw service status (outer circle)
    if running:
        # Draw outer circle (service running)
        d.ellipse([(center_x - radius, center_y - radius),
                  (center_x + radius, center_y + radius)],
                 outline=1, fill=0)
        
        # Draw inner dot for generation status
        if generating:
            d.ellipse([(center_x - radius//3, center_y - radius//3),
                      (center_x + radius//3, center_y + radius//3)],
                     outline=1, fill=1)
    else:
        # Draw X for service not running
        d.line([(center_x - radius, center_y - radius),
               (center_x + radius, center_y + radius)],
              fill=1, width=3)
        d.line([(center_x - radius, center_y + radius),
               (center_x + radius, center_y - radius)],
              fill=1, width=3)
    
    return img


def main():
    """Main loop for the LLM status display."""
    global oled
    
    # Set up signal handlers for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("LLM Status Indicator - Press Ctrl+C to exit")
    
    try:
        # Initialize the display
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        print("Display initialized")
        
        while True:
            try:
                # Get LLM status
                status = get_llm_status()
                
                # Draw and display the status icon
                frame = draw_status_icon(status['running'], status['generating'])
                oled.display_image(frame)
                
                # Update every 2 seconds
                time.sleep(2)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(5)  # Wait before retrying
                
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()