import serial
import threading
import time
from serial.tools import list_ports
from .enums import MouseButton

class SerialTransport:
    baud_change_command = bytearray([0xDE, 0xAD, 0x05, 0x00, 0xA5, 0x00, 0x09, 0x3D, 0x00])

    _button_map = {
        0: MouseButton.LEFT,
        1: MouseButton.RIGHT,
        2: MouseButton.MIDDLE,
        3: MouseButton.MOUSE4,
        4: MouseButton.MOUSE5,
    }

    def __init__(self, fallback, debug=False, send_init=True):
        self._fallback_com_port = fallback
        self.debug = debug
        self.send_init = send_init
        self._button_callback = None
        self._last_mask = 0
        self._lock = threading.Lock()
        self._is_connected = False
        self._stop_event = threading.Event()
        self._listener_thread = None
        self._button_states = {btn: False for btn in self._button_map.values()}
        self._pause_listener = False

        self.port = self.find_com_port()
        if not self.port:
            raise Exception("Makcu device not found. Please specify a port explicitly.")

        self.baudrate = 115200
        self.serial = None

    def receive_response(self, sent_command: str = "") -> str:
        lines = []
        try:
            for _ in range(3):
                line = self.serial.readline().decode(errors="ignore").strip()
                if not line:
                    break
                lines.append(line)
        except serial.SerialException as e:
            raise Exception(f"Error reading from serial port: {e}")

        command_clean = sent_command.strip()
        if command_clean in lines:
            lines.remove(command_clean)
        if "OK" in lines:
            lines.remove("OK")

        return "\n".join(lines)

    def set_button_callback(self, callback):
        self._button_callback = callback

    def _log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        print(entry, flush=True)

    def find_com_port(self):
        self._log("Searching for CH343 device...")

        for port in list_ports.comports():
            if "VID:PID=1A86:55D3" in port.hwid:
                self._log(f"Device found: {port.device}")
                return port.device

        if self._fallback_com_port:
            self._log(f"Device not found. Falling back to specified port: {self._fallback_com_port}")
            return self._fallback_com_port
        else:
            self._log("Fallback port not specified or invalid.")
            return None

    def _open_serial_port(self, port, baud_rate):
        try:
            self._log(f"Trying to open {port} at {baud_rate} baud.")
            return serial.Serial(port, baud_rate, timeout=0.05)
        except serial.SerialException:
            self._log(f"Failed to open {port} at {baud_rate} baud.")
            return None

    def _change_baud_to_4M(self):
        if self.serial and self.serial.is_open:
            self._log("Sending baud rate switch command to 4M.")
            self.serial.write(self.baud_change_command)
            self.serial.flush()
            self.serial.baudrate = 4000000
            time.sleep(0.05)
            self._log("Switched to 4M baud successfully.")
            return True
        return False

    def connect(self):
        if self._is_connected:
            self._log("Already connected.")
            return
        self.serial = self._open_serial_port(self.port, 115200)
        if not self.serial:
            raise Exception(f"Failed to connect to {self.port} at 115200.")
        self._log(f"Connected to {self.port} at 115200.")
        if not self._change_baud_to_4M():
            raise Exception("Failed to switch to 4M baud.")
        self._is_connected = True
        if self.send_init:
            self._stop_event.clear()
            self._listener_thread = threading.Thread(target=self._listen, kwargs={"debug": self.debug}, daemon=True)
            with self._lock:
                self.serial.write(b"km.buttons(1)\r")
                self.serial.flush()
                self._log("Sended init command: km.buttons(1)")
            self._listener_thread.start()

    def disconnect(self):
        if self.send_init:
            self._stop_event.set()
            if self._listener_thread:
                self._listener_thread.join()
        with self._lock:
            if self.serial and self.serial.is_open:
                self.serial.close()
            self.serial = None
            self._is_connected = False
            self._log("Disconnected.")

    def is_connected(self):
        return self._is_connected

    def send_command(self, command, expect_response=False):
        if not self._is_connected or not self.serial or not self.serial.is_open:
            raise Exception("Serial connection not open.")
        
        with self._lock:
            self._pause_listener = True

            if expect_response:
                self.serial.reset_input_buffer()

            self.serial.write(command.encode("ascii") + b"\r\n")
            self.serial.flush()

            if expect_response:
                response = self.receive_response(sent_command=command)
                if not response:
                    raise Exception(f"No response from device for command: {command}")
                return response

            self.serial.reset_input_buffer()
            self._pause_listener = False

    def get_button_states(self):
        return dict(self._button_states)

    def get_button_mask(self) -> int:
        mask = 0
        for bit, button in self._button_map.items():
            if self._button_states.get(button, False):
                mask |= (1 << bit)
        return mask

    def enable_button_monitoring(self, enable: bool = True):
        self.send_command("km.buttons(1)" if enable else "km.buttons(0)")

    def _get_button_command(self, button: MouseButton, action: str) -> str:
        command_map = {
            MouseButton.LEFT: "ml",
            MouseButton.RIGHT: "mr",
            MouseButton.MIDDLE: "mm",
            MouseButton.MOUSE4: "ms1",
            MouseButton.MOUSE5: "ms2",
        }
        if button not in command_map:
            raise ValueError(f"Unsupported button: {button}")
        return f"km.catch_{command_map[button]}({action})"

    def catch_button(self, button: MouseButton):
        command = self._get_button_command(button, "0")
        self.send_command(command)

    def read_captured_clicks(self, button: MouseButton) -> int:
        command = self._get_button_command(button, "")
        result = self.send_command(command, expect_response=True)
        try:
            return int(result.strip())
        except (ValueError, TypeError):
            return 0

    def _listen(self, debug=False):
        self._log("Started listener thread")
        self._last_mask = 0

        while self._is_connected and not self._stop_event.is_set():
            if self._pause_listener:
                time.sleep(0.001)
                continue

            try:
                byte = self.serial.read(1)
                if not byte:
                    continue

                current_mask = byte[0]

                if current_mask > 0b11111 or current_mask in [0x0D, 0x0A]:
                    continue
                    
                if current_mask != self._last_mask:
                    changed_bits = current_mask ^ self._last_mask
                    for bit, button_enum in self._button_map.items():
                        if changed_bits & (1 << bit):
                            is_pressed = (current_mask & (1 << bit)) > 0
                            self._button_states[button_enum] = is_pressed
                            if self._button_callback:
                                self._button_callback(button_enum, is_pressed)

                    self._last_mask = current_mask

                    if debug:
                        pressed = [
                            btn.name for btn, state in self._button_states.items() if state
                        ]
                        status = ", ".join(pressed) if pressed else "No buttons"
                        self._log(f"Mask: 0x{current_mask:02X} -> {status}")

            except serial.SerialException as e:
                self._log(f"Serial error in listener: {e}")
                break
            except Exception as e:
                self._log(f"Unexpected error in listener: {e}")

            time.sleep(0.001)

        self._log("Listener thread exiting")
