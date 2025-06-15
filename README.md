# rk-gpio
Make GPIO work on Rockchip Orange Pi CM5

# Specs

Orange Pi CM5 + Orange Pi OS + Orange Pi CM5 Tablet Board

# Setup

1. turn on I2C in Orange Pi OS
- sudo orangepi-config
- turn on i2c5

2. Follow and install instruction here: https://github.com/thomasvunguyen/WiringPi-Python-OP

Note: This allows (and encourage) to use a virtual python environment

3. Connect OLED to CM5 Tablet Board:
- VCC to 5V
- GND to GND
- SCL to SCL (pin 3)
- SDA to SDA (pin 5)


