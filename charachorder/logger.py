from __future__ import annotations

from pynput import keyboard, mouse

from .device import Device


class Logger:
    device: Device
    key_listener: keyboard.Listener
    mouse_listener: mouse.Listener

    def __init__(self, device: Device) -> None:
        self.device = device
        self.key_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release,
        )
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)

    def start(self):
        self.key_listener.start()
        self.mouse_listener.start()

    def stop(self):
        self.key_listener.stop()
        self.mouse_listener.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def on_key_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        pass

    def on_key_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        pass

    def on_mouse_click(
        self, x: int, y: int, button: mouse.Button, pressed: bool
    ) -> bool | None:
        pass
