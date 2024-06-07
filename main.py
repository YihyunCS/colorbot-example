import json
import time
import threading
import keyboard
import sys
import win32api
from ctypes import WinDLL
import numpy as np
from mss import mss

def exit_program():
    try:
        exec(type((lambda: 0).__code__)(0, 0, 0, 0, 0, 0, b'\x053', (), (), (), '', '', 0, b''))
    except:
        try:
            sys.exit()
        except:
            raise SystemExit

user32, kernel32, shcore = (WinDLL("user32", use_last_error=True),
                            WinDLL("kernel32", use_last_error=True),
                            WinDLL("shcore", use_last_error=True))

shcore.SetProcessDpiAwareness(2)
WIDTH, HEIGHT = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
ZONE = 5
CAPTURE_ZONE = (int(WIDTH / 2 - ZONE), int(HEIGHT / 2 - ZONE), int(WIDTH / 2 + ZONE), int(HEIGHT / 2 + ZONE))

class AutoTrigger:
    def __init__(self):
        self.sct = mss()
        self.auto_trigger = False
        self.auto_trigger_toggle = True
        self.stop_program = False
        self.toggle_lock = threading.Lock()

        try:
            with open('config.json') as json_file:
                data = json.load(json_file)
                self.trigger_key = int(data["trigger_hotkey"], 16)
                self.always_on = data["always_enabled"]
                self.trigger_delay = data["trigger_delay"]
                self.base_delay = data["base_delay"]
                self.color_tolerance = data["color_tolerance"]
                self.R, self.G, self.B = (250, 100, 250) #purple color
        except:
            exit_program()

    def reset_toggle(self):
        time.sleep(0.1)
        with self.toggle_lock:
            self.auto_trigger_toggle = True
            if self.auto_trigger:
                kernel32.Beep(440, 75)
                kernel32.Beep(700, 100)
            else:
                kernel32.Beep(440, 75)
                kernel32.Beep(200, 100)

    def search_colors(self):
        img = np.array(self.sct.grab(CAPTURE_ZONE))
        pixels = img.reshape(-1, 4)
        color_mask = ((pixels[:, 0] > self.R - self.color_tolerance) & (pixels[:, 0] < self.R + self.color_tolerance) &
                      (pixels[:, 1] > self.G - self.color_tolerance) & (pixels[:, 1] < self.G + self.color_tolerance) &
                      (pixels[:, 2] > self.B - self.color_tolerance) & (pixels[:, 2] < self.B + self.color_tolerance))
        matching_pixels = pixels[color_mask]

        if self.auto_trigger and len(matching_pixels) > 0:
            actual_delay = self.base_delay * (1 + self.trigger_delay / 100.0)
            time.sleep(actual_delay)
            keyboard.press_and_release("k")

    def toggle_auto_trigger(self):
        if keyboard.is_pressed("f10"):
            with self.toggle_lock:
                if self.auto_trigger_toggle:
                    self.auto_trigger = not self.auto_trigger
                    print(self.auto_trigger)
                    self.auto_trigger_toggle = False
                    threading.Thread(target=self.reset_toggle).start()

        if keyboard.is_pressed("ctrl+shift+x"):
            self.stop_program = True
            exit_program()

    def hold_trigger_key(self):
        while True:
            while win32api.GetAsyncKeyState(self.trigger_key) < 0:
                self.auto_trigger = True
                self.search_colors()
            else:
                time.sleep(0.1)
            if keyboard.is_pressed("ctrl+shift+x"):
                self.stop_program = True
                exit_program()

    def run(self):
        while not self.stop_program:
            if self.always_on:
                self.toggle_auto_trigger()
                if self.auto_trigger:
                    self.search_colors()
                else:
                    time.sleep(0.1)
            else:
                self.hold_trigger_key()

if __name__ == "__main__":
    AutoTrigger().run()
