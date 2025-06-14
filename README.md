# rk-gpio
Make GPIO work on Rockchip Orange Pi CM5

# Specs

Orange Pi CM5 + Orange Pi OS + Orange Pi CM5 Tablet Board

# Setup

1. turn on I2C in Orange Pi OS
- sudo orangepi-config
- turn on i2c5

2. Follow and install instruction here: https://github.com/lanefu/WiringPi-Python-OP

Note: This installs on global python, not in a virtual environment

3. Connect OLED to CM5 Tablet Board:
- VCC to 5V
- GND to GND
- SCL to SCL (pin 3)
- SDA to SDA (pin 5)


