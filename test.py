#!/usr/bin/env python3
"""
Working OLED test for Orange Pi CM5
Bus 5, Address 0x3C (your working configuration)
"""

import smbus2
import time
from PIL import Image, ImageDraw, ImageFont

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

def test_basic_display():
    """Test basic OLED functionality"""
    print("=" * 50)
    print("Orange Pi CM5 - OLED Test")
    print("Bus 5, Address 0x3C")
    print("=" * 50)
    
    try:
        # Create OLED object
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
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
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
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

def display_thinking_symbol():
    """Display a symbol representing thinking on the OLED"""
    print("Displaying thinking symbol...")
    print("Press Ctrl+C to stop")
    
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
        # Create thinking symbol (brain with thought bubbles)
        image = Image.new('1', (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        # Draw brain outline
        draw.ellipse((44, 20, 84, 50), outline=1)
        
        # Draw brain wrinkles/folds
        draw.arc((44, 20, 84, 40), 0, 180, fill=1)
        draw.arc((44, 30, 84, 50), 180, 360, fill=1)
        draw.arc((54, 20, 74, 50), 0, 360, fill=1)
        
        # Draw thought bubbles
        draw.ellipse((90, 15, 100, 25), outline=1)
        draw.ellipse((100, 5, 115, 20), outline=1)
        draw.ellipse((115, 10, 125, 20), outline=1)
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        draw.text((25, 5), "THINKING", font=font, fill=1)
        
        oled.display_image(image)
        
        # Keep display on until interrupted with better exception handling
        try:
            while True:
                time.sleep(0.1)
        finally:  # This ensures cleanup happens even if interrupted
            try:
                oled.clear()
                oled.close()
                print("\nThinking symbol stopped. Display cleared.")
            except:
                print("\nCouldn't clean up display properly, but exiting.")
                
    except Exception as e:
        print(f"Error: {e}")
        try:
            oled.close()
        except:
            pass

def display_listening_symbol():
    """Display a symbol representing listening on the OLED"""
    print("Displaying listening symbol...")
    print("Press Ctrl+C to stop")
    
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
        # Create listening symbol (ear with sound waves)
        image = Image.new('1', (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        # Draw a clearer ear shape
        # Outer ear shape
        points = [
            (60, 15), (50, 20), (45, 30), (45, 40), 
            (50, 50), (60, 55), (65, 55), (70, 50)
        ]
        draw.polygon(points, outline=1)
        
        # Inner ear canal
        draw.ellipse((62, 40, 72, 50), outline=1)
        
        # Draw sound waves approaching the ear
        for i in range(3):
            x_offset = i * 10
            draw.arc((30-x_offset, 30, 50-x_offset, 50), 300, 60, fill=1, width=1)
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        draw.text((35, 5), "LISTENING", font=font, fill=1)
        
        oled.display_image(image)
        
        # Keep display on until interrupted
        try:
            while True:
                time.sleep(0.1)
        finally:  # This ensures cleanup happens even if interrupted
            try:
                oled.clear()
                oled.close()
                print("\nListening symbol stopped. Display cleared.")
            except:
                print("\nCouldn't clean up display properly, but exiting.")
                
    except Exception as e:
        print(f"Error: {e}")
        try:
            oled.close()
        except:
            pass

def display_speaking_symbol():
    """Display a symbol representing speaking on the OLED"""
    print("Displaying speaking symbol...")
    print("Press Ctrl+C to stop")
    
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
        # Create speaking symbol (face with mouth and sound waves)
        image = Image.new('1', (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        # Draw face outline
        draw.ellipse((45, 15, 85, 55), outline=1)
        
        # Draw eyes
        draw.ellipse((55, 25, 60, 30), fill=1)  # Left eye
        draw.ellipse((70, 25, 75, 30), fill=1)  # Right eye
        
        # Draw open mouth
        draw.ellipse((58, 35, 72, 45), outline=1)
        draw.chord((58, 35, 72, 45), 0, 180, fill=1)
        
        # Draw sound waves emanating from mouth
        for i in range(3):
            x_offset = i * 8
            # Sound waves on the right side
            draw.line([(85+x_offset, 30), (85+x_offset, 40)], fill=1)
            draw.line([(85+x_offset, 30), (90+x_offset, 25)], fill=1)
            draw.line([(85+x_offset, 40), (90+x_offset, 45)], fill=1)
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        draw.text((35, 5), "SPEAKING", font=font, fill=1)
        
        oled.display_image(image)
        
        # Keep display on until interrupted with better exception handling
        try:
            while True:
                time.sleep(0.1)
        finally:  # This ensures cleanup happens even if interrupted
            try:
                oled.clear()
                oled.close()
                print("\nSpeaking symbol stopped. Display cleared.")
            except:
                print("\nCouldn't clean up display properly, but exiting.")
                
    except Exception as e:
        print(f"Error: {e}")
        try:
            oled.close()
        except:
            pass

def display_silly_face():
    """Display a silly face with tongue out on the OLED"""
    print("Displaying silly face...")
    print("Press Ctrl+C to stop")
    
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
        # Create silly face
        image = Image.new('1', (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        # Draw face outline
        draw.ellipse((40, 10, 90, 60), outline=1)
        
        # Draw eyes (crossed)
        draw.line([(50, 20), (60, 30)], fill=1)  # Left eye X (line 1)
        draw.line([(50, 30), (60, 20)], fill=1)  # Left eye X (line 2)
        draw.line([(70, 20), (80, 30)], fill=1)  # Right eye X (line 1)
        draw.line([(70, 30), (80, 20)], fill=1)  # Right eye X (line 2)
        
        # Draw silly mouth with tongue
        draw.arc((50, 35, 80, 55), 0, 180, fill=1)  # Smile
        draw.rectangle((60, 45, 70, 58), fill=1)   # Tongue sticking out
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        draw.text((35, 0), "SILLY FACE", font=font, fill=1)
        
        oled.display_image(image)
        
        # Keep display on until interrupted with better exception handling
        try:
            while True:
                time.sleep(0.1)
        finally:  # This ensures cleanup happens even if interrupted
            try:
                oled.clear()
                oled.close()
                print("\nSilly face stopped. Display cleared.")
            except:
                print("\nCouldn't clean up display properly, but exiting.")
                
    except Exception as e:
        print(f"Error: {e}")
        try:
            oled.close()
        except:
            pass

def display_surprised_face():
    """Display a surprised face on the OLED"""
    print("Displaying surprised face...")
    print("Press Ctrl+C to stop")
    
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
        # Create surprised face
        image = Image.new('1', (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        # Draw face outline
        draw.ellipse((40, 10, 90, 60), outline=1)
        
        # Draw eyes (wide open circles)
        draw.ellipse((48, 20, 58, 30), outline=1)  # Left eye
        draw.ellipse((72, 20, 82, 30), outline=1)  # Right eye
        
        # Draw eyebrows (raised)
        draw.line([(46, 15), (60, 12)], fill=1)  # Left eyebrow
        draw.line([(70, 12), (84, 15)], fill=1)  # Right eyebrow
        
        # Draw mouth (small O shape)
        draw.ellipse((58, 40, 72, 54), outline=1)
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 0), "SURPRISED FACE", font=font, fill=1)
        
        oled.display_image(image)
        
        # Keep display on until interrupted with better exception handling
        try:
            while True:
                time.sleep(0.1)
        finally:  # This ensures cleanup happens even if interrupted
            try:
                oled.clear()
                oled.close()
                print("\nSurprised face stopped. Display cleared.")
            except:
                print("\nCouldn't clean up display properly, but exiting.")
                
    except Exception as e:
        print(f"Error: {e}")
        try:
            oled.close()
        except:
            pass

def display_cool_face():
    """Display a cool face with sunglasses on the OLED"""
    print("Displaying cool face...")
    print("Press Ctrl+C to stop")
    
    try:
        oled = SSD1306(i2c_bus=1, i2c_addr=0x3C)
        
        # Create cool face
        image = Image.new('1', (128, 64), 0)
        draw = ImageDraw.Draw(image)
        
        # Draw face outline
        draw.ellipse((40, 10, 90, 60), outline=1)
        
        # Draw sunglasses
        draw.rectangle((45, 20, 85, 30), fill=1)  # Sunglasses frame
        draw.line([(65, 20), (65, 30)], fill=0)   # Bridge of sunglasses
        
        # Draw cool smile
        draw.arc((50, 35, 80, 50), 0, 180, fill=1)  # Smile
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            font = ImageFont.load_default()
        
        draw.text((30, 0), "COOL FACE", font=font, fill=1)
        
        oled.display_image(image)
        
        # Keep display on until interrupted with better exception handling
        try:
            while True:
                time.sleep(0.1)
        finally:  # This ensures cleanup happens even if interrupted
            try:
                oled.clear()
                oled.close()
                print("\nCool face stopped. Display cleared.")
            except:
                print("\nCouldn't clean up display properly, but exiting.")
                
    except Exception as e:
        print(f"Error: {e}")
        try:
            oled.close()
        except:
            pass

def funky_art():
    """Menu for selecting which symbol or face to display"""
    print("Funky Art Options:")
    print("1. Thinking Symbol")
    print("2. Listening Symbol")
    print("3. Speaking Symbol")
    print("4. Silly Face")
    print("5. Surprised Face")
    print("6. Cool Face")
    
    choice = input("Enter choice (1-6): ").strip()
    
    if choice == "1":
        display_thinking_symbol()
    elif choice == "2":
        display_listening_symbol()
    elif choice == "3":
        display_speaking_symbol()
    elif choice == "4":
        display_silly_face()
    elif choice == "5":
        display_surprised_face()
    elif choice == "6":
        display_cool_face()
    else:
        print("Invalid choice. Displaying thinking symbol by default...")
        display_thinking_symbol()

if __name__ == "__main__":
    print("Orange Pi CM5 OLED Test")
    print("1. Basic test")
    print("2. System monitor")
    print("3. Thinking Symbol")
    print("4. Listening Symbol")
    print("5. Speaking Symbol")
    print("6. Silly Face")
    print("7. Surprised Face")
    print("8. Cool Face")
    
    choice = input("Enter choice (1-8): ").strip()
    
    if choice == "1":
        test_basic_display()
    elif choice == "2":
        system_monitor()
    elif choice == "3":
        display_thinking_symbol()
    elif choice == "4":
        display_listening_symbol()
    elif choice == "5":
        display_speaking_symbol()
    elif choice == "6":
        display_silly_face()
    elif choice == "7":
        display_surprised_face()
    elif choice == "8":
        display_cool_face()
    else:
        print("Invalid choice. Running basic test...")
        test_basic_display()
