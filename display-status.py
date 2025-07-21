#!/usr/bin/env python3
"""display-status.py – OLED LLM Status Indicator

Displays status of the LLM service and generation state using animated faces.
"""
import smbus2
from PIL import Image, ImageDraw, ImageFont
import time
import signal
import sys
import requests
import math

# --- Global Configuration ---
# Adjust this value to move the face up or down.
FACE_VERTICAL_OFFSET = 15
# Adjust this value to move the text up or down.
TEXT_VERTICAL_OFFSET = 5

# Booleans
SERVICE_RUNNING = False
GENERATING = False
CONNECTED = False

# API Configuration
LLM_HEALTH_URL = "http://localhost:1306/health"
LUNA_ACTIVE_URL = "http://localhost:1309/luna/active"  # New endpoint
API_TIMEOUT = 2  # seconds

# Display Configuration
WIDTH, HEIGHT = 128, 64

# Global OLED instance for cleanup
oled = None


class SSD1306:
    """A class to control the SSD1306 OLED display over I2C."""
    def __init__(self, i2c_bus=1, i2c_addr=0x3C, width=128, height=64):
        self.bus_num = i2c_bus
        self.addr = i2c_addr
        self.width = width
        self.height = height
        self.pages = height // 8
        
        self.bus = smbus2.SMBus(self.bus_num)
        print(f"Using I2C bus {self.bus_num}, address 0x{self.addr:02X}")
        
        self.init_display()
    
    def write_cmd(self, cmd):
        self.bus.write_byte_data(self.addr, 0x00, cmd)
        time.sleep(0.001)
        
    def write_data(self, data):
        self.bus.write_byte_data(self.addr, 0x40, data)
    
    def init_display(self):
        init_cmds = [
            0xAE, 0x20, 0x00, 0xB0, 0xC8, 0x00, 0x10, 0x40, 0x81, 0xFF,
            0xA1, 0xA6, 0xA8, 0x3F, 0xA4, 0xD3, 0x00, 0xD5, 0xF0, 0xD9,
            0x22, 0xDA, 0x12, 0xDB, 0x20, 0x8D, 0x14, 0xAF
        ]
        for cmd in init_cmds:
            self.write_cmd(cmd)
    
    def clear(self):
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x00)
            self.write_cmd(0x10)
            for _ in range(self.width):
                self.write_data(0x00)
    
    def display_image(self, image):
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
        self.bus.close()

# --- Face Drawing Functions ---

def get_font(size=10):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except IOError:
        return ImageFont.load_default()

def draw_text_centered(draw, text, y_pos, oled_width, font):
    try:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
    except AttributeError:
        text_width, _ = draw.textsize(text, font=font)
    text_x = (oled_width - text_width) // 2
    draw.text((text_x, y_pos), text, font=font, fill=1)

def display_startup_face(oled):
    image = Image.new('1', (oled.width, oled.height), 0)
    draw = ImageDraw.Draw(image)
    font = get_font(12)
    eye_y_center = 42 - FACE_VERTICAL_OFFSET
    eye_height_max = 20
    for i in range(1, eye_height_max + 1, 2):
        draw.rectangle((0, 0, oled.width, oled.height), fill=0)
        draw_text_centered(draw, "Booting...", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
        y0, y1 = eye_y_center - i // 2, eye_y_center + i // 2
        draw.ellipse((24, y0, 44, y1), fill=1)
        draw.ellipse((84, y0, 104, y1), fill=1)
        oled.display_image(image)
        time.sleep(0.05)
    time.sleep(1)

def draw_services_ready_frame(draw, frame_index):
    font = get_font(12)
    left_eye = (24, 32 - FACE_VERTICAL_OFFSET, 44, 52 - FACE_VERTICAL_OFFSET)
    right_eye = (84, 32 - FACE_VERTICAL_OFFSET, 104, 52 - FACE_VERTICAL_OFFSET)
    mouth_points = [(54, 56 - FACE_VERTICAL_OFFSET), (64, 62 - FACE_VERTICAL_OFFSET), (74, 56 - FACE_VERTICAL_OFFSET)]
    pupil_positions = [-4, 0, 4, 0]
    pos = pupil_positions[frame_index % len(pupil_positions)]
    
    draw_text_centered(draw, "Ready", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
    draw.ellipse(left_eye, fill=1)
    draw.ellipse(right_eye, fill=1)
    draw.line(mouth_points, fill=1, width=1)
    draw.rectangle((34 + pos, 40 - FACE_VERTICAL_OFFSET, 34 + pos + 2, 44 - FACE_VERTICAL_OFFSET), fill=0)
    draw.rectangle((94 + pos, 40 - FACE_VERTICAL_OFFSET, 94 + pos + 2, 44 - FACE_VERTICAL_OFFSET), fill=0)

def display_connection_established_face(draw):
    font = get_font(12)
    left_eye = (24, 32 - FACE_VERTICAL_OFFSET, 44, 52 - FACE_VERTICAL_OFFSET)
    right_eye = (84, 32 - FACE_VERTICAL_OFFSET, 104, 52 - FACE_VERTICAL_OFFSET)
    mouth_arc = (48, 52 - FACE_VERTICAL_OFFSET, 80, 62 - FACE_VERTICAL_OFFSET)
    
    draw_text_centered(draw, "Connected!", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
    draw.ellipse(left_eye, fill=1)
    draw.ellipse(right_eye, fill=1)
    draw.arc(mouth_arc, 0, 180, fill=1, width=2)

def draw_running_llm_frame(draw, frame_index):
    font = get_font(12)
    eye_y_top = 36 - FACE_VERTICAL_OFFSET
    eye_y_bottom = 48 - FACE_VERTICAL_OFFSET
    left_eye_box = (24, eye_y_top, 44, eye_y_bottom)
    right_eye_box = (84, eye_y_top, 104, eye_y_bottom)
    mouth_points = [(54, 56 - FACE_VERTICAL_OFFSET), (64, 62 - FACE_VERTICAL_OFFSET), (74, 56 - FACE_VERTICAL_OFFSET)]
    angle = frame_index * 15

    eye_content = Image.new('1', (WIDTH, HEIGHT), 0)
    draw_eye = ImageDraw.Draw(eye_content)
    for i in range(4):
        y_offset = 6 * math.sin(math.radians(angle + i * 45))
        y_pos = 42 - FACE_VERTICAL_OFFSET + y_offset
        if eye_y_top < y_pos < eye_y_bottom:
            draw_eye.line((left_eye_box[0], y_pos, left_eye_box[2], y_pos), fill=1)
            draw_eye.line((right_eye_box[0], y_pos, right_eye_box[2], y_pos), fill=1)

    draw_text_centered(draw, "Thinking...", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
    draw.line(mouth_points, fill=1, width=1)
    
    mask = Image.new('1', (WIDTH, HEIGHT), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse(left_eye_box, fill=1)
    draw_mask.ellipse(right_eye_box, fill=1)
    
    temp_img = Image.new('1', (WIDTH, HEIGHT), 0)
    temp_img.paste(eye_content, (0, 0), mask)
    draw.bitmap((0,0), temp_img, fill=1)

def draw_offline_face(draw):
    font = get_font(12)
    draw_text_centered(draw, "Offline", 2 - TEXT_VERTICAL_OFFSET, oled.width, font)
    d = draw
    d.line((24, 32 - FACE_VERTICAL_OFFSET, 44, 52 - FACE_VERTICAL_OFFSET), fill=1, width=3)
    d.line((24, 52 - FACE_VERTICAL_OFFSET, 44, 32 - FACE_VERTICAL_OFFSET), fill=1, width=3)
    d.line((84, 32 - FACE_VERTICAL_OFFSET, 104, 52 - FACE_VERTICAL_OFFSET), fill=1, width=3)
    d.line((84, 52 - FACE_VERTICAL_OFFSET, 104, 32 - FACE_VERTICAL_OFFSET), fill=1, width=3)
    d.arc((48, 60 - FACE_VERTICAL_OFFSET, 80, 70 - FACE_VERTICAL_OFFSET), 180, 360, fill=1, width=2)

# --- Main Application Logic ---

def cleanup():
    global oled
    if oled:
        try:
            oled.clear()
            oled.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    sys.exit(0)

def signal_handler(sig, frame):
    cleanup()

def get_llm_status():
    global SERVICE_RUNNING, GENERATING
    try:
        response = requests.get(LLM_HEALTH_URL, timeout=API_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            SERVICE_RUNNING = True
            GENERATING = data.get('generation_status') == 'generating'
        else:
            SERVICE_RUNNING = False
            GENERATING = False
    except requests.RequestException:
        SERVICE_RUNNING = False
        GENERATING = False

def check_luna_active():
    global CONNECTED
    try:
        response = requests.get(LUNA_ACTIVE_URL, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        CONNECTED = data.get('active', False)
    except (requests.RequestException, ValueError, KeyError):
        CONNECTED = False

def main():
    global oled
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("LLM Status Indicator - Press Ctrl+C to exit")
    
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        display_startup_face(oled)
        
        frame_index = 0

        while True:
            get_llm_status()
            check_luna_active()
            
            image = Image.new('1', (oled.width, oled.height), 0)
            draw = ImageDraw.Draw(image)

            if not SERVICE_RUNNING:
                draw_offline_face(draw)
                time.sleep(2)
            elif CONNECTED:
                display_connection_established_face(draw)
                time.sleep(2) # Show connected face for 2 seconds then re-evaluate
            elif GENERATING:
                draw_running_llm_frame(draw, frame_index)
                time.sleep(0.02)
            else: # Service is running, not generating, not connected
                draw_services_ready_frame(draw, frame_index)
                time.sleep(0.5)

            oled.display_image(image)
            frame_index += 1
                
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
