# pymakcu

[![PyPI version](https://badge.fury.io/py/pymakcu.svg)](https://badge.fury.io/py/pymakcu)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python library for programmatically controlling the Makcu custom USB mouse emulator device via a COM port. This library provides a high-level and convenient API for automating mouse actions.

## Key Features

-   **Auto-Connect:** The library automatically finds the device by its VID/PID.
-   **Full Mouse Control:** Move, click, hold buttons, and scroll.
-   **Advanced Movement:** Includes smooth linear movement and Bezier curve paths.
-   **Human-like Clicks:** Emulate clicks with realistic, randomized delays.
-   **Locking:** Programmatically lock mouse movement axes (X/Y) or individual buttons.
-   **Real-time Monitoring:** Get live button state updates using callbacks.
-   **Click Capturing:** Intercept physical button presses on the device.

## Installation

```bash
pip install pymakcu
```
This will also install the required `pyserial` dependency.

## Quick Start

The following example shows the most basic usage: connect, move, click, and disconnect.

```python
from pymakcu import create_controller, MouseButton

# Auto-detects the port and connects to the device
controller = create_controller()

# Move the cursor 100 pixels to the right and 50 pixels down
controller.move(100, 50)

# Perform a left-click
controller.click(MouseButton.LEFT)

# Always disconnect to release the COM port
controller.disconnect()
```

## API Guide & Examples

### 1. Connection Management

-   `create_controller(fallback_com_port="")`: The main factory function. Finds, connects to, and initializes the device. If auto-detection fails, you can specify a port like `"COM3"` or `"/dev/ttyUSB0"`.
-   `controller.disconnect()`: Closes the serial connection. **It is crucial to call this when you are done.**
-   `controller.is_connected()`: Returns `True` if the device is connected.

### 2. Mouse Button Control

The `MouseButton` enum is used to specify a button (`LEFT`, `RIGHT`, `MIDDLE`, `MOUSE4`, `MOUSE5`).

-   `controller.click(button)`: Performs a full press and release action.
-   `controller.press(button)`: Presses and holds a button down.
-   `controller.release(button)`: Releases a previously held button.

**Example: Drag-and-Drop**
```python
# Press and hold the left button
controller.press(MouseButton.LEFT)

# Move the mouse while the button is held
controller.move(200, 100)

# Release the button to complete the drag
controller.release(MouseButton.LEFT)
```

### 3. Human-like Clicks

The `click_human_like` method simulates human behavior by adding small, random delays.

-   `controller.click_human_like(button, count=1, profile="normal", jitter=0)`
    -   `count`: The number of clicks to perform.
    -   `profile`: A timing profile (`"normal"`, `"fast"`, `"slow"`).
    -   `jitter`: Adds a minor, random mouse movement (`±jitter` pixels) before each click to appear more natural.

**Example:**
```python
# Perform 3 fast right-clicks with slight mouse "jitter"
controller.click_human_like(MouseButton.RIGHT, count=3, profile="fast", jitter=2)
```

### 4. Cursor Movement

-   `controller.move(dx, dy)`: Instantly moves the cursor by a relative `dx`, `dy` offset.
-   `controller.move_smooth(dx, dy, segments)`: Moves the cursor along a straight line, broken into `segments` smaller steps for a smooth visual effect.
-   `controller.move_bezier(dx, dy, segments, ctrl_x, ctrl_y)`: Moves along a Bezier curve. The `ctrl_x` and `ctrl_y` parameters define the curve's shape relative to the start point.

**Example:**
```python
# Move smoothly in a diagonal line
controller.move_smooth(150, 150, segments=25)

# Move along a gentle arc
controller.move_bezier(dx=200, dy=0, segments=30, ctrl_x=100, ctrl_y=100)
```

### 5. Locking Axes and Buttons

You can programmatically prevent the device from sending certain inputs.

-   `controller.lock_mouse_x(True)` / `controller.lock_mouse_x(False)`
-   `controller.lock_left(True)` / `controller.lock_left(False)` (and for `right`, `middle`, etc.)
-   `controller.get_all_lock_states()`: Returns a dictionary of the current lock states.

**Example:**
```python
# Lock the Y-axis
controller.lock_mouse_y(True)

# This command will now only move the cursor horizontally
controller.move(100, 100)

# Unlock the Y-axis to restore normal movement
controller.lock_mouse_y(False)
```

### 6. Real-time Button Monitoring (Callbacks)

The library can monitor physical button presses on the device in the background and trigger a function you provide for each event.

**Example:**
```python
from pymakcu import create_controller, MouseButton
import time

# 1. Define your callback function. It must accept two arguments:
#    the button enum and a boolean for its pressed state.
def on_button_event(button: MouseButton, is_pressed: bool):
    action = "pressed" if is_pressed else "released"
    print(f"Event: Button {button.name} was {action}")

controller = create_controller()

# 2. Register your function as the callback
controller.set_button_callback(on_button_event)

print("Monitoring enabled. Press buttons on your device for 10 seconds...")

# 3. Keep the script alive for the background thread to receive events
time.sleep(10)

controller.disconnect()
print("Monitoring stopped.")
```

### 7. Getting Device Information

-   `controller.get_firmware_version()`: Returns the device's firmware version string.
-   `controller.get_device_info()`: Returns a dictionary with COM port info, VID/PID, and connection status.
-   `controller.get_button_states()`: Returns a dictionary of current button states.

**Example:**
```python
info = controller.get_device_info()
print(f"Connected to {info.get('port')} (VID={info.get('vid')}, PID={info.get('pid')})")

version = controller.get_firmware_version()
print(f"Firmware version: {version}")
```