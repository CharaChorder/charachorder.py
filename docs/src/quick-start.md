# Quickstart

This page gives a brief introduction to the library assuming you have already [installed it](./installation.md).

## Minimal

For most use cases, you'll likely want to use the existing classes and their methods as provided in the library. To get started, simply import the `CharaChorder` class that represents any CharaChorder device.

```py
from charachorder import CharaChorder

for device in CharaChorder.list_devices():
    print(device)
```

The `list_devices` method finds and returns the list of CC devices connected to your system. Note that it will, in most cases, return a subclass of `CharaChorder`, such as `CharaChorderOne`, `CharaChorderLite`, etc.

You can also list out specific CC devices:

```py
from charachorder import CharaChorderLite

for device in CharaChorderLite.list_devices():
    print(device)
```

The `list_devices` method here will ignore any other CC device and will only try to find CCL devices.

### Sending serial commands

All of the serial API commands are wrapped in methods of each CC class. Although, to send these commands, you must first connect to the serial port where the device is connected. Don't worry, the library provides 2 ways you can do this:

**Method 1:** - recommended

Using the `with` context manager, you don't need to worry about opening or closing the serial connection, it will do it automatically for you!

```py
with device:
    # run commands here
```

**Method 2:**

Some use cases may require the serial connection to be used over a long period and frequently toggling it may become expensive. For that, you can manually manage the connection using the `open` and `close` methods.

```py
device.open()
# run commands here
device.close()
```

Some examples are:

```py
with device:
    # ID
    id: str = device.get_id()

    # VERSION
    version: str = device.get_version()

    # CML C0
    total_chords: int = device.get_chordmap_count()
```

A full list of methods is given in the reference guide (TODO).
