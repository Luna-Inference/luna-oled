#!/usr/bin/env python3
"""display-status.py – OLED LLM Status Indicator

Displays status of the LLM service and generation state using icons.
- Green circle: Service running
- Red X: Service not running
- Dot: Generating
- No dot: Idle
"""
import smbus2
from PIL import Image, ImageDraw, ImageFont
import time
import signal
import sys
import requests

# Import the display driver
# from test import SSD1306  # noqa: E402 – local import on purpose

# API Configuration
LLM_HEALTH_URL = "http://localhost:1306/health"
API_TIMEOUT = 2  # seconds

# Display Configuration
WIDTH, HEIGHT = 128, 64

# Global OLED instance for cleanup
oled = None


class SSD1306:
    def __init__(self, i2c_bus=1, i2c_addr=0x3C, width=128, height=64):
        self.bus_num = i2c_bus
        self.addr = i2c_addr
        self.width = width
        self.height = height
        self.pages = height // 8
        
        self.bus = smbus2.SMBus(self.bus_num)
        print(f"Using I2C bus {self.bus_num}, address 0x{self.addr:02X}")
        
        # Initialize display
        self.init_display()
    
    def write_cmd(self, cmd):
        """Send command to display"""
        self.bus.write_byte_data(self.addr, 0x00, cmd)
        time.sleep(0.001)
        
    def write_data(self, data):
        """Send data to display"""
        if isinstance(data, list):
            for byte in data:
                self.bus.write_byte_data(self.addr, 0x40, byte)
        else:
            self.bus.write_byte_data(self.addr, 0x40, data)
    
    def init_display(self):
        """Initialize SSD1306 display"""
        init_cmds = [
            0xAE,  # Display OFF
            0x20,  # Set Memory Addressing Mode
            0x00,  # Horizontal Addressing Mode
            0xB0,  # Set Page Start Address
            0xC8,  # Set COM Output Scan Direction
            0x00,  # Set Low Column Address
            0x10,  # Set High Column Address
            0x40,  # Set Start Line Address
            0x81,  # Set Contrast Control
            0xFF,  # Maximum contrast
            0xA1,  # Set Segment Re-map
            0xA6,  # Set Normal Display
            0xA8,  # Set Multiplex Ratio
            0x3F,  # 1/64 duty
            0xA4,  # Output follows RAM content
            0xD3,  # Set Display Offset
            0x00,  # No offset
            0xD5,  # Set Display Clock Divide Ratio
            0xF0,  # Set Divide Ratio
            0xD9,  # Set Pre-charge Period
            0x22,  # Pre-charge period
            0xDA,  # Set COM Pins Configuration
            0x12,  # COM pins configuration
            0xDB,  # Set VCOMH
            0x20,  # VCOMH
            0x8D,  # Set DC-DC enable
            0x14,  # DC-DC enable
            0xAF   # Display ON
        ]
        
        print("Initializing OLED...")
        for cmd in init_cmds:
            self.write_cmd(cmd)
        print("OLED initialized!")
    
    def clear(self):
        """Clear the display"""
        print("Clearing display...")
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)  # Set page address
            self.write_cmd(0x00)         # Set low column address
            self.write_cmd(0x10)         # Set high column address
            
            # Send zeros for this page
            for col in range(self.width):
                self.write_data(0x00)
        print("Display cleared!")
    
    def display_image(self, image):
        """Display PIL image on OLED"""
        print("Displaying image...")
        
        # Convert image to 1-bit and resize if needed
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))
        
        if image.mode != '1':
            image = image.convert('1')
        
        # Convert to display buffer and send page by page
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)  # Set page address
            self.write_cmd(0x00)         # Set low column address
            self.write_cmd(0x10)         # Set high column address
            
            for x in range(self.width):
                byte = 0
                for bit in range(8):
                    y = page * 8 + bit
                    if y < self.height:
                        pixel = image.getpixel((x, y))
                        if pixel:
                            byte |= 1 << bit
                self.write_data(byte)
        
        print("Image displayed!")
    
    def close(self):
        """Close I2C connection"""
        self.bus.close()


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