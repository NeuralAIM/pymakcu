import random
import time
from .mouse import Mouse
from .connection import SerialTransport
from .enums import MouseButton

class MakcuController:
    def __init__(self, fallback_com_port, debug=False, send_init=True):
        self.transport = SerialTransport(fallback_com_port, debug=debug, send_init=send_init)
        self.mouse = Mouse(self.transport)

    def connect(self):
        self.transport.connect()

    def disconnect(self):
        self.transport.disconnect()

    def is_connected(self):
        return self.transport.is_connected()

    def click(self, button: MouseButton):
        self.mouse.press(button)
        self.mouse.release(button)

    def move(self, dx: int, dy: int):
        self.mouse.move(dx, dy)

    def scroll(self, delta: int):
        self.mouse.scroll(delta)

    def move_smooth(self, dx: int, dy: int, segments: int):
        self.mouse.move_smooth(dx, dy, segments)

    def move_bezier(self, dx: int, dy: int, segments: int, ctrl_x: int, ctrl_y: int):
        self.mouse.move_bezier(dx, dy, segments, ctrl_x, ctrl_y)

    def lock_mouse_x(self, lock: bool):
        self.mouse.lock_x(lock)

    def lock_mouse_y(self, lock: bool):
        self.mouse.lock_y(lock)

    def lock_left(self, lock: bool):
        self.mouse.lock_left(lock)

    def lock_middle(self, lock: bool):
        self.mouse.lock_middle(lock)

    def lock_right(self, lock: bool):
        self.mouse.lock_right(lock)

    def lock_side1(self, lock: bool):
        self.mouse.lock_side1(lock)

    def lock_side2(self, lock: bool):
        self.mouse.lock_side2(lock)

    def spoof_serial(self, serial: str):
        self.mouse.spoof_serial(serial)

    def reset_serial(self):
        self.mouse.reset_serial()

    def get_device_info(self):
        return self.mouse.get_device_info()

    def get_firmware_version(self):
        return self.mouse.get_firmware_version()

    def get_button_mask(self) -> int:
        return self.transport.get_button_mask()

    def is_button_locked(self, button: MouseButton) -> bool:
        return self.mouse.is_button_locked(button)

    def capture(self, button: MouseButton):
        self.transport.catch_button(button)

    def get_captured_clicks(self, button: MouseButton) -> int:
        return self.transport.read_captured_clicks(button)

    def click_human_like(self, button: MouseButton, count: int = 1,
                         profile: str = "normal", jitter: int = 0):
        timing_profiles = {
            "normal": (60, 120, 100, 180),
            "fast": (30, 60, 50, 100),
            "slow": (100, 180, 150, 300),
        }

        if profile not in timing_profiles:
            raise ValueError(f"Invalid profile: {profile}. Choose from {list(timing_profiles.keys())}")

        min_down, max_down, min_wait, max_wait = timing_profiles[profile]

        for _ in range(count):
            if jitter > 0:
                dx = random.randint(-jitter, jitter)
                dy = random.randint(-jitter, jitter)
                self.mouse.move(dx, dy)

            self.mouse.press(button)
            time.sleep(random.uniform(min_down, max_down) / 1000.0)
            self.mouse.release(button)
            time.sleep(random.uniform(min_wait, max_wait) / 1000.0)

    def enable_button_monitoring(self, enable: bool = True):
        self.transport.enable_button_monitoring(enable)

    def set_button_callback(self, callback):
        self.transport.set_button_callback(callback)

    def get_all_lock_states(self) -> dict:
        return self.mouse.get_all_lock_states()

    def press(self, button: MouseButton):
        self.mouse.press(button)

    def release(self, button: MouseButton):
        self.mouse.release(button)

    def get_button_states(self) -> dict:
        return self.transport.get_button_states()

    def is_button_pressed(self, button: MouseButton) -> bool:
        return self.transport.get_button_states().get(button, False)