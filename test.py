#!/usr/bin/env python3
"""
Working OLED test for Orange Pi CM5 to display a "Cute Face"
with a blinking left eye and other animations.
Bus: 1, Address: 0x3C (adjust if your configuration is different)
"""

import smbus2
import time
import math
from PIL import Image, ImageDraw, ImageFont

# --- Global Configuration ---
# Adjust this value to move the face up or down.
# A larger number moves the face higher on the screen.
FACE_VERTICAL_OFFSET = 15
# Adjust this value to move the text up or down.
# A larger number moves the text higher on the screen.
TEXT_VERTICAL_OFFSET = 5

class SSD1306:
    """A class to control the SSD1306 OLED display over I2C."""
    def __init__(self, i2c_bus=1, i2c_addr=0x3C, width=128, height=64):
        """Initializes the display."""
        self.bus_num = i2c_bus
        self.addr = i2c_addr
        self.width = width
        self.height = height
        self.pages = height // 8
        
        self.bus = smbus2.SMBus(self.bus_num)
        print(f"Using I2C bus {self.bus_num}, address 0x{self.addr:02X}")
        
        # Initialize the display hardware
        self.init_display()
    
    def write_cmd(self, cmd):
        """Sends a command byte to the display."""
        self.bus.write_byte_data(self.addr, 0x00, cmd)
        time.sleep(0.001)
        
    def write_data(self, data):
        """Sends a data byte to the display."""
        self.bus.write_byte_data(self.addr, 0x40, data)
    
    def init_display(self):
        """Runs the initialization sequence for the SSD1306."""
        init_cmds = [
            0xAE,   # Display OFF
            0x20,   # Set Memory Addressing Mode
            0x00,   # Horizontal Addressing Mode
            0xB0,   # Set Page Start Address
            0xC8,   # Set COM Output Scan Direction (flipped)
            0x00,   # Set Low Column Address
            0x10,   # Set High Column Address
            0x40,   # Set Start Line Address
            0x81,   # Set Contrast Control
            0xFF,   # Maximum contrast
            0xA1,   # Set Segment Re-map (column 127 is mapped to SEG0)
            0xA6,   # Set Normal Display
            0xA8,   # Set Multiplex Ratio
            0x3F,   # 1/64 duty
            0xA4,   # Output follows RAM content
            0xD3,   # Set Display Offset
            0x00,   # No offset
            0xD5,   # Set Display Clock Divide Ratio
            0xF0,   # Set Divide Ratio
            0xD9,   # Set Pre-charge Period
            0x22,   # Pre-charge period
            0xDA,   # Set COM Pins Hardware Configuration
            0x12,   # Alternative COM pin config
            0xDB,   # Set VCOMH Deselect Level
            0x20,   # VCOMH level
            0x8D,   # Set DC-DC enable
            0x14,   # DC-DC enable
            0xAF    # Display ON
        ]
        
        print("Initializing OLED...")
        for cmd in init_cmds:
            self.write_cmd(cmd)
        print("OLED initialized!")
    
    def clear(self):
        """Clears the entire display."""
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x00)
            self.write_cmd(0x10)
            for _ in range(self.width):
                self.write_data(0x00)
    
    def display_image(self, image):
        """Displays a 1-bit PIL Image on the screen."""
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))
        if image.mode != '1':
            image = image.convert('1')
        
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x00)
            self.write_cmd(0x10)
            
            for x in range(self.width):
                byte = 0
                for bit in range(8):
                    y = page * 8 + bit
                    if y < self.height:
                        pixel = image.getpixel((x, y))
                        if pixel:
                            byte |= (1 << bit)
                self.write_data(byte)
    
    def close(self):
        """Turns off the display and closes the I2C connection."""
        self.clear()
        self.write_cmd(0xAE)
        self.bus.close()
        print("I2C connection closed.")

def get_font(size=10):
    """Loads a font, with a fallback to the default."""
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except IOError:
        print("Default font not found. Using built-in font.")
        return ImageFont.load_default()

def draw_text_centered(draw, text, y_pos, oled_width, font):
    """Helper function to draw centered text."""
    try:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
    except AttributeError:
        text_width, _ = draw.textsize(text, font=font)
    
    text_x = (oled_width - text_width) // 2
    draw.text((text_x, y_pos), text, font=font, fill=1)

def display_startup_face(oled):
    """Awakening face: eyes slowly open with text."""
    print("Displaying Startup Face... Press Ctrl+C to stop.")
    image = Image.new('1', (oled.width, oled.height), 0)
    draw = ImageDraw.Draw(image)
    font = get_font(12)
    
    eye_y_center = 42 - FACE_VERTICAL_OFFSET
    eye_height_max = 20

    for i in range(1, eye_height_max + 1, 2):
        draw.rectangle((0, 0, oled.width, oled.height), fill=0)
        draw_text_centered(draw, "Booting...", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
        
        y0 = eye_y_center - i // 2
        y1 = eye_y_center + i // 2
        draw.ellipse((24, y0, 44, y1), fill=1)
        draw.ellipse((84, y0, 104, y1), fill=1)
        
        oled.display_image(image)
        time.sleep(0.05)

    time.sleep(2)

def display_services_ready_face(oled):
    """Alert face: eyes look side to side with text."""
    print("Displaying Services Ready Face... Press Ctrl+C to stop.")
    image = Image.new('1', (oled.width, oled.height), 0)
    draw = ImageDraw.Draw(image)
    font = get_font(12)
    
    left_eye = (24, 32 - FACE_VERTICAL_OFFSET, 44, 52 - FACE_VERTICAL_OFFSET)
    right_eye = (84, 32 - FACE_VERTICAL_OFFSET, 104, 52 - FACE_VERTICAL_OFFSET)
    mouth_points = [(54, 56 - FACE_VERTICAL_OFFSET), (64, 62 - FACE_VERTICAL_OFFSET), (74, 56 - FACE_VERTICAL_OFFSET)]
    pupil_positions = [-4, 0, 4, 0]
    
    while True:
        for pos in pupil_positions:
            draw.rectangle((0, 0, oled.width, oled.height), fill=0)
            draw_text_centered(draw, "Ready", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
            draw.ellipse(left_eye, fill=1)
            draw.ellipse(right_eye, fill=1)
            draw.line(mouth_points, fill=1, width=1)
            
            draw.rectangle((34 + pos, 40 - FACE_VERTICAL_OFFSET, 34 + pos + 2, 44 - FACE_VERTICAL_OFFSET), fill=0)
            draw.rectangle((94 + pos, 40 - FACE_VERTICAL_OFFSET, 94 + pos + 2, 44 - FACE_VERTICAL_OFFSET), fill=0)

            oled.display_image(image)
            time.sleep(0.5)

def display_connection_established_face(oled):
    """Happy face: a smile appears with text."""
    print("Displaying Connection Established Face... Press Ctrl+C to stop.")
    image = Image.new('1', (oled.width, oled.height), 0)
    draw = ImageDraw.Draw(image)
    font = get_font(12)

    # Standard eye size
    left_eye = (24, 32 - FACE_VERTICAL_OFFSET, 44, 52 - FACE_VERTICAL_OFFSET)
    right_eye = (84, 32 - FACE_VERTICAL_OFFSET, 104, 52 - FACE_VERTICAL_OFFSET)
    # Happy smile
    mouth_arc = (48, 52 - FACE_VERTICAL_OFFSET, 80, 62 - FACE_VERTICAL_OFFSET)

    draw.rectangle((0, 0, oled.width, oled.height), fill=0)
    draw_text_centered(draw, "Connected!", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
    draw.ellipse(left_eye, fill=1)
    draw.ellipse(right_eye, fill=1)
    draw.arc(mouth_arc, 0, 180, fill=1, width=2)
    
    oled.display_image(image)
    while True:
        time.sleep(1)

def display_running_llm_face(oled):
    """Thinking face: eyes narrow and data flows with text."""
    print("Displaying Running LLM Face... Press Ctrl+C to stop.")
    image = Image.new('1', (oled.width, oled.height), 0)
    draw = ImageDraw.Draw(image)
    font = get_font(12)

    eye_y_top = 36 - FACE_VERTICAL_OFFSET
    eye_y_bottom = 48 - FACE_VERTICAL_OFFSET
    left_eye_box = (24, eye_y_top, 44, eye_y_bottom)
    right_eye_box = (84, eye_y_top, 104, eye_y_bottom)
    mouth_points = [(54, 56 - FACE_VERTICAL_OFFSET), (64, 62 - FACE_VERTICAL_OFFSET), (74, 56 - FACE_VERTICAL_OFFSET)]
    angle = 0

    while True:
        eye_content = Image.new('1', (oled.width, oled.height), 0)
        draw_eye = ImageDraw.Draw(eye_content)

        for i in range(4):
            y_offset = 6 * math.sin(math.radians(angle + i * 45))
            y_pos = 42 - FACE_VERTICAL_OFFSET + y_offset
            if eye_y_top < y_pos < eye_y_bottom:
                draw_eye.line((left_eye_box[0], y_pos, left_eye_box[2], y_pos), fill=1)
                draw_eye.line((right_eye_box[0], y_pos, right_eye_box[2], y_pos), fill=1)

        draw.rectangle((0, 0, oled.width, oled.height), fill=0)
        draw_text_centered(draw, "Thinking...", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
        draw.line(mouth_points, fill=1, width=1)
        
        mask = Image.new('1', (oled.width, oled.height), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse(left_eye_box, fill=1)
        draw_mask.ellipse(right_eye_box, fill=1)
        image.paste(eye_content, (0, 0), mask)

        oled.display_image(image)
        angle = (angle + 15) % 360
        time.sleep(0.02)

def run_animation(animation_func):
    """Generic runner for face animations."""
    oled = None
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        animation_func(oled)
    except KeyboardInterrupt:
        print("\nStopping animation.")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        if oled:
            oled.close()
        print("Program finished.")

# --- Restored Original Functions for Compatibility ---

def test_basic_display():
    """Tests basic OLED functionality with text."""
    print("=" * 50)
    print("Orange Pi CM5 - Basic OLED Test")
    print("=" * 50)
    oled = None
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        oled.clear()
        image = Image.new('1', (oled.width, oled.height), 0)
        draw = ImageDraw.Draw(image)
        font = get_font(12)
        draw.text((0, 0), "Orange Pi CM5", font=font, fill=1)
        draw.text((0, 16), "OLED Test OK!", font=font, fill=1)
        draw.text((0, 32), f"Time: {time.strftime('%H:%M:%S')}", font=font, fill=1)
        oled.display_image(image)
        print("✅ SUCCESS! Check your OLED display.")
        print("Display will stay on for 10 seconds...")
        time.sleep(10)
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        if oled:
            oled.close()
        print("Test complete!")

def display_cute_face():
    """Displays the 'Cute Face' on the OLED until interrupted."""
    print("Displaying Cute Face... Press Ctrl+C to stop.")
    oled = None
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        image = Image.new('1', (oled.width, oled.height), 0)
        draw = ImageDraw.Draw(image)
        left_eye_coords = (24, 32 - FACE_VERTICAL_OFFSET, 44, 52 - FACE_VERTICAL_OFFSET)
        right_eye_coords = (84, 32 - FACE_VERTICAL_OFFSET, 104, 52 - FACE_VERTICAL_OFFSET)
        mouth_points = [(54, 56 - FACE_VERTICAL_OFFSET), (64, 62 - FACE_VERTICAL_OFFSET), (74, 56 - FACE_VERTICAL_OFFSET)]
        draw.ellipse(left_eye_coords, fill=1)
        draw.ellipse(right_eye_coords, fill=1)
        draw.line(mouth_points, fill=1, width=1)
        oled.display_image(image)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping face display.")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    finally:
        if oled:
            oled.close()
        print("Program finished.")

def display_blinking_face():
    """Displays a cute face with a blinking left eye."""
    run_animation(lambda oled: _blinking_face_loop(oled))

def _blinking_face_loop(oled):
    """The actual animation loop for the blinking face."""
    image = Image.new('1', (oled.width, oled.height), 0)
    draw = ImageDraw.Draw(image)
    left_eye_coords = (24, 32 - FACE_VERTICAL_OFFSET, 44, 52 - FACE_VERTICAL_OFFSET)
    right_eye_coords = (84, 32 - FACE_VERTICAL_OFFSET, 104, 52 - FACE_VERTICAL_OFFSET)
    mouth_points = [(54, 56 - FACE_VERTICAL_OFFSET), (64, 62 - FACE_VERTICAL_OFFSET), (74, 56 - FACE_VERTICAL_OFFSET)]

    while True:
        draw.rectangle((0, 0, oled.width, oled.height), fill=0)
        draw.ellipse(left_eye_coords, fill=1)
        draw.ellipse(right_eye_coords, fill=1)
        draw.line(mouth_points, fill=1, width=1)
        oled.display_image(image)
        time.sleep(0.85) 

        draw.rectangle(left_eye_coords, fill=0)
        oled.display_image(image)
        time.sleep(0.15)

if __name__ == "__main__":
    print("🍊 Orange Pi CM5 OLED Menu")
    print("1. Startup Face")
    print("2. Services Ready Face")
    print("3. Connection Established Face")
    print("4. Running LLM Face")
    print("-" * 20)
    print("5. Basic hardware test")
    print("6. Display 'Cute Face' (static)")
    print("7. Display 'Cute Face' (blinking)")
    
    choice = input("Enter choice (1-7): ").strip()
    
    animation_map = {
        "1": display_startup_face,
        "2": display_services_ready_face,
        "3": display_connection_established_face,
        "4": display_running_llm_face,
    }
    
    if choice in animation_map:
        run_animation(animation_map[choice])
    elif choice == "5":
        test_basic_display()
    elif choice == "6":
        display_cute_face()
    elif choice == "7":
        display_blinking_face()
    else:
        print("Invalid choice. Exiting.")
