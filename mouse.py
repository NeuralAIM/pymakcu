from .enums import MouseButton
from serial.tools import list_ports

class Mouse:
    def __init__(self, transport):
        self.transport = transport

    def _send_button_command(self, button: MouseButton, state: int):
        command_map = {
            MouseButton.LEFT: "left",
            MouseButton.RIGHT: "right",
            MouseButton.MIDDLE: "middle",
        }
        if button not in command_map:
            raise Exception(f"Unsupported button: {button}")
        self.transport.send_command(f"km.{command_map[button]}({state})")

    def press(self, button: MouseButton):
        self._send_button_command(button, 1)

    def release(self, button: MouseButton):
        self._send_button_command(button, 0)

    def move(self, x: int, y: int):
        self.transport.send_command(f"km.move({x},{y})")

    def move_smooth(self, x: int, y: int, segments: int):
        self.transport.send_command(f"km.move({x},{y},{segments})")

    def move_bezier(self, x: int, y: int, segments: int, ctrl_x: int, ctrl_y: int):
        self.transport.send_command(f"km.move({x},{y},{segments},{ctrl_x},{ctrl_y})")

    def scroll(self, delta: int):
        self.transport.send_command(f"km.wheel({delta})")

    def lock_left(self, lock: bool):
        self.transport.send_command(f"km.lock_ml({int(lock)})")

    def lock_middle(self, lock: bool):
        self.transport.send_command(f"km.lock_mm({int(lock)})")

    def lock_right(self, lock: bool):
        self.transport.send_command(f"km.lock_mr({int(lock)})")

    def lock_side1(self, lock: bool):
        self.transport.send_command(f"km.lock_ms1({int(lock)})")

    def lock_side2(self, lock: bool):
        self.transport.send_command(f"km.lock_ms2({int(lock)})")

    def lock_x(self, lock: bool):
        self.transport.send_command(f"km.lock_mx({int(lock)})")

    def lock_y(self, lock: bool):
        self.transport.send_command(f"km.lock_my({int(lock)})")

    def spoof_serial(self, serial: str):
        self.transport.send_command(f"km.serial('{serial}')")

    def reset_serial(self):
        self.transport.send_command("km.serial(0)")

    def get_device_info(self) -> dict:
        port_name = self.transport.port
        port_info = next((p for p in list_ports.comports() if p.device == port_name), None)

        return {
            "port": port_name,
            "description": getattr(port_info, 'description', "Unknown"),
            "vid": hex(port_info.vid) if hasattr(port_info, 'vid') and port_info.vid is not None else "Unknown",
            "pid": hex(port_info.pid) if hasattr(port_info, 'pid') and port_info.pid is not None else "Unknown",
            "isConnected": self.transport.is_connected(),
        }

    def get_firmware_version(self) -> str:
        return self.transport.send_command("km.version()", expect_response=True)

    def _get_lock_command(self, target: str) -> str:
        command_map = {
            "X": "mx", "Y": "my",
            "LEFT": "ml", "RIGHT": "mr", "MIDDLE": "mm",
            "MOUSE4": "ms1", "MOUSE5": "ms2",
        }
        key = target.upper()
        if key not in command_map:
            raise ValueError(f"Unsupported lock target: {target}")
        return f"km.lock_{command_map[key]}()"

    def is_locked(self, target: str) -> bool:
        command = self._get_lock_command(target)
        try:
            result = self.transport.send_command(command, expect_response=True)
            return result.strip() == "1"
        except:
            return False

    def is_button_locked(self, button: MouseButton) -> bool:
        return self.is_locked(button.name)

    def get_all_lock_states(self) -> dict:
        return {
            target: self.is_locked(target)
            for target in ["X", "Y", "LEFT", "RIGHT", "MIDDLE", "MOUSE4", "MOUSE5"]
        }