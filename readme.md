# charachorder.py

A wrapper for CharaChorder's Serial API written in Python

> **Warning:**
> This project is in beta; breaking changes will occur without notice. Please wait for v1.0.0

## Features

- Supports all major versions of Python3.
- Exhaustive list of commands as in the [Serial API](https://docs.charachorder.com/SerialAPI.html).
- Events (coming soon).

## Installation

**Python 3.8 or higher is required.**

```sh
# Linux/macOS
python3 -m pip install -U charachorder.py

# Windows
py -3 -m pip install -U charachorder.py
```

To install the development version, run the following:
```sh
git clone https://github.com/GetPsyched/charachorder.py
cd charachorder.py
python3 -m pip install -U .
```

## Usage

```py
from charachorder import CharaChorder

for device in CharaChorder.list_devices():
    # Method 1
    with device:
        print(device.get_id())

    # Method 2
    device.open()
    print(device.get_id())
    device.close()
```

## Links

- [Documentation](https://getpsyched.github.io/charachorder.py)
- [CharaChorder's Official Discord Server](https://discord.gg/QZJeZGtznG)
- [Serial API](https://docs.charachorder.com/SerialAPI.html)
