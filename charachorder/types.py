from enum import Enum


class KeymapCode(Enum):
    primary = 0xA1
    secondary = 0xA2
    tertiary = 0xA3


class ParameterCode(Enum):
    enable_serial_header = 0x01
    enable_serial_logging = 0x02
    enable_serial_debugging = 0x03
    enable_serial_raw = 0x04
    enable_serial_chord = 0x05
    enable_serial_keyboard = 0x06
    enable_serial_mouse = 0x07
    enable_usb_hid_keyboard = 0x11
    enable_character_entry = 0x12
    gui_ctrl_swap_mode = 0x13
    key_scan_duration = 0x14
    key_debounce_press_duration = 0x15
    key_debounce_release_duration = 0x16
    keyboard_output_character_microsecond_delays = 0x17
    enable_usb_hid_mouse = 0x21
    slow_mouse_speed = 0x22
    fast_mouse_speed = 0x23
    enable_active_mouse = 0x24
    mouse_scroll_speed = 0x25
    mouse_poll_duration = 0x26
    enable_chording = 0x31
    enable_chording_character_counter_timeout = 0x32
    chording_character_counter_timeout_timer = 0x33
    chord_detection_press_tolerance = 0x34
    chord_detection_release_tolerance = 0x35
    enable_spurring = 0x41
    enable_spurring_character_counter_timeout = 0x42
    spurring_character_counter_timeout_timer = 0x43
    enable_arpeggiates = 0x51
    arpeggiate_tolerance = 0x52
    enable_compound_chording_ = 0x61
    compound_tolerance = 0x64
    led_brightness = 0x81
    led_color_code = 0x82
    enable_led_key_highlight_ = 0x83
    enable_leds = 0x84
    operating_system = 0x91
    enable_realtime_feedback = 0x92
    enable_charachorder_ready_on_startup = 0x93
