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

# Service
```
sudo cp -r luna-oled.service /etc/systemd/system/luna-oled.service

sudo systemctl daemon-reload          # Reload systemd configurations
sudo systemctl enable luna-oled.service   # Auto-start on boot
sudo systemctl start luna-oled.service    # Start service now

sudo systemctl stop luna-oled.service     # Stop the service
sudo systemctl restart luna-oled.service  # Restart the service
sudo systemctl disable luna-oled.service  # Remove from boot startup

systemctl status luna-oled.service        # Current status and recent logs
journalctl -u luna-oled.service          # View all logs for this service
journalctl -u luna-oled.service -f       # Follow logs in real-time
journalctl -u luna-oled.service --since today  # View today's logs only
journalctl -u luna-oled.service --since "2024-01-01" --until "2024-01-02"  # Date range
```

# Setup for service

```
# Check if i2c group exists
getent group i2c || sudo groupadd i2c

# Add luna to i2c group
sudo usermod -aG i2c luna

# Create udev rule for I2C
echo 'SUBSYSTEM=="i2c-dev", GROUP="i2c", MODE="0660"' | sudo tee /etc/udev/rules.d/99-i2c.rules

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Verify permissions
ls -l /dev/i2c-*
```
```
# Reload systemd
sudo systemctl daemon-reload

# Restart the service
sudo systemctl restart luna-oled.service

# Check status
sudo systemctl status luna-oled.service

# View logs
sudo journalctl -u luna-oled.service -f
```