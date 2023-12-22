# charachorder.py

A wrapper for CharaChorder's Serial API written in Python

## Usage

```py
from charachorder import CCDevice, CCSerial

for device in CCDevice.list_devices():
    with CCSerial(device) as cc_serial:
        print(cc_serial.get_device_id())
```
