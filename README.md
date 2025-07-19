# rk-gpio
Make GPIO work on Rockchip Orange Pi CM5

# Specs

Orange Pi CM5 + Orange Pi OS + Orange Pi CM5 Tablet Board

# Setup

1. turn on I2C in Orange Pi OS
- sudo orangepi-config
- turn on i2c5

2. Follow and install instruction here: https://github.com/Luna-Inference/WiringPi-Python-OP
```
git clone --recursive https://github.com/ThomasVuNguyen/WiringPi-Python-OP.git
sudo apt update
sudo apt install build-essential gcc g++  # generic compiler
# or for explicit cross-compiler name
sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu
sudo apt-get install python3-dev python3-setuptools swig
python3 -m venv myenv
source myenv/bin/activate
cd WiringPi-Python-OP
./build.sh
cd ..
```
```
# Test installation
python -c "import wiringpi; print('WiringPi successfully installed!')"
```

Note: This allows (and encourage) to use a virtual python environment

3. Connect OLED to CM5 Tablet Board:
- VCC to 5V
- GND to GND
- SCL to SCL (pin 3)
- SDA to SDA (pin 5)


# Test

```
sudo myenv/bin/python test.py
```
