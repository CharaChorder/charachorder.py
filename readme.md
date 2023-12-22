# charachorder.py

A wrapper for CharaChorder's Serial API written in Python

> **Warning**
> This project is in beta; breaking changes will occur without notice. Please wait for v1.0.0

## Usage

```py
from charachorder import CCDevice, CCSerial

for device in CCDevice.list_devices():
    with CCSerial(device) as cc_serial:
        print(cc_serial.get_device_id())
```
