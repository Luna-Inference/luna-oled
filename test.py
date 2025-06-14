#!/usr/bin/env python3
"""
Working OLED test for Orange Pi CM5
Bus 5, Address 0x3C (your working configuration)
"""

import smbus2
import time
from PIL import Image, ImageDraw, ImageFont

class SSD1306:
    def __init__(self, i2c_bus=5, i2c_addr=0x3C, width=128, height=64):
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

def test_basic_display():
    """Test basic OLED functionality"""
    print("=" * 50)
    print("Orange Pi CM5 - OLED Test")
    print("Bus 5, Address 0x3C")
    print("=" * 50)
    
    try:
        # Create OLED object
        oled = SSD1306(i2c_bus=5, i2c_addr=0x3C)
        
        # Clear display
        oled.clear()
        time.sleep(1)
        
        # Create test image
        image = Image.new('1', (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        # Try to load a font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Draw text
        draw.text((0, 0), "Orange Pi CM5", font=font, fill=1)
        draw.text((0, 16), "OLED Working!", font=font, fill=1)
        draw.text((0, 32), "Bus 5, 0x3C", font=font, fill=1)
        draw.text((0, 48), time.strftime("%H:%M:%S"), font=font, fill=1)
        
        # Display image
        oled.display_image(image)
        
        print("✅ SUCCESS! Check your OLED display!")
        print("The display should show:")
        print("- Orange Pi CM5")
        print("- OLED Working!")
        print("- Bus 5, 0x3C")
        print("- Current time")
        
        # Keep display on for 10 seconds
        print("\nDisplay will stay on for 10 seconds...")
        time.sleep(10)
        
        # Clear and close
        oled.clear()
        oled.close()
        print("Test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check your wiring and connections")

def system_monitor():
    """Continuous system monitor display"""
    import subprocess
    
    print("Starting system monitor...")
    print("Press Ctrl+C to stop")
    
    try:
        oled = SSD1306(i2c_bus=5, i2c_addr=0x3C)
        
        while True:
            # Create image
            image = Image.new('1', (128, 64), 0)
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            # Get system info
            try:
                # CPU temperature
                temp_output = subprocess.check_output("cat /sys/class/thermal/thermal_zone0/temp", shell=True)
                cpu_temp = f"{int(temp_output)/1000:.1f}°C"
            except:
                cpu_temp = "N/A"
            
            try:
                # Memory usage
                mem_info = subprocess.check_output("free -m | grep '^Mem'", shell=True).decode().split()
                mem_used = int(mem_info[2])
                mem_total = int(mem_info[1])
                mem_percent = f"{(mem_used/mem_total)*100:.0f}%"
            except:
                mem_percent = "N/A"
            
            # Draw information
            draw.text((0, 0), "Orange Pi CM5", font=font, fill=1)
            draw.text((0, 12), f"Temp: {cpu_temp}", font=font, fill=1)
            draw.text((0, 24), f"RAM: {mem_percent}", font=font, fill=1)
            draw.text((0, 36), f"Time: {time.strftime('%H:%M:%S')}", font=font, fill=1)
            draw.text((0, 48), f"Date: {time.strftime('%m/%d')}", font=font, fill=1)
            
            # Display
            oled.display_image(image)
            time.sleep(1)
            
    except KeyboardInterrupt:
        oled.clear()
        oled.close()
        print("\nMonitor stopped. Display cleared.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Orange Pi CM5 OLED Test")
    print("1. Basic test")
    print("2. System monitor")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        test_basic_display()
    elif choice == "2":
        system_monitor()
    else:
        print("Invalid choice. Running basic test...")
        test_basic_display()
