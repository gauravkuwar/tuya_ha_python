# Tuya + HomeKit Integration with Python + Raspberry Pi

This is a simple script that is used to control Tuya lightbulbs/switches from the Apple Home app. Currently, only offers on/off functionality. I wanted to keep this as bare minimum as possible, but you can modify the code as you see fit for your use case. Additionally, I control the Tuya devices locally, so it doesn't access the Tuya cloud every time I turn on a light, and keeps things in the local network.

## Why did I make this script?

Firstly, there are lightbulbs and switches for Apple Homekit, but these are generally more expensive than Tuya or other IoT devices.

Home Assistant can do this same thing, which is what I was initially using. However, it often broke, and you had to install the entire HASS OS on the raspberry pi, making it unusable for other purposes. Using docker, also didn't work well for me. Overall, Home Assistant had too much unnecessary functionality, for this very simple use case.

## Setup

### Getting Tuya device local-keys

This is the most difficult part, but this awesome video helped me get the local keys, note that this process is free.

[HOW TO - Setup Local Tuya in Home Assistant](https://www.youtube.com/watch?v=vq2L9c5hDfQ)

### Setting up raspberry pi

I used the HAP-python and tinytuya for this script. Keep these things in mind when installing these 2 libraries.

1. Make sure to install __64-bit__ OS on Raspberry Pi. (I ran into an error installing cryptography for HAP-python)
2. Installing [HAP-python](https://github.com/ikalchev/HAP-python) requires some other linux depencies. 

### Storing Device Info

I store all device info in `devices.json` file. To set it up keep in mind:

- `ip_addr` is the IP address of the IoT device. HAP-python can give you this by scanning.
- `version` for lightbulbs the version is 3.3 and for switches, it is 3.1
- `id` you can also get from HAP-python scan, or in the Tuya cloud.

### Running script as a service

__Note: you won't get the QR image when you run this as a service, but you can just type the code__

Create a new config file for service:

```
sudo vi /etc/systemd/system/pyhap.service
```

Here is my configuration the script is in `/home/pi/tuya_homekit/tuya_ha_service.py`, `pi` is my username, and `Restart=always` starts the service on boot.

```
[Unit]
Description=PyHAP Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 -m tuya_ha_service.py 
WorkingDirectory=/home/pi/tuya_homekit/
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Then to start the service:

```
sudo systemctl enable pyhap.service
sudo systemctl start pyhap.service
```

Here are some other helpful commands:

```
sudo systemctl status pyhap.service # get status (This is where you get setup code) and some logs
sudo systemctl stop pyhap.service # stop the service
sudo journalctl -u pyhap.service # see all logs
```

## Some more things to keep in mind

- You can't add the hub on iOS devices, this is just how homekit works. So, you have to add it on one device and invite people with different apple ids to the home, so they can use the devices.

- You __cannot__ have Tuya app (or other tuya connections) open at the same time as this service. It will cause the service to not work, but will go back to normal after you close the app.
