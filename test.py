import tkinter as tk
from tkinter import filedialog
import threading
import time
import ctypes
import mido
import pygame.midi
import math

# Define XINPUT_VIBRATION structure for XInput
class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", ctypes.c_ushort),
        ("wRightMotorSpeed", ctypes.c_ushort)
    ]

# Load XInput DLL
xinput = ctypes.windll.xinput1_3
XInputSetState = xinput.XInputSetState
XInputSetState.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_VIBRATION)]
XInputSetState.restype = ctypes.c_uint

def set_vibration(controller, left, right):
    vibration = XINPUT_VIBRATION(int(left * 65535), int(right * 65535))
    XInputSetState(controller, ctypes.byref(vibration))

def stop_vibration():
    set_vibration(0, 0, 0)

def rumble_pattern(pattern, level, duration, motor='both'):
    interval = 0.01
    steps = int(duration / interval)
    for i in range(steps):
        if pattern == 'pulse':
            intensity = level if i % 4 < 2 else 0
        elif pattern == 'fade':
            intensity = level * (1.0 - i / steps)
        elif pattern == 'sine':
            intensity = level * (0.5 + 0.5 * math.sin(2 * math.pi * (i / steps)))
        elif pattern == 'linear ramp':
            intensity = level * (i / steps)
        elif pattern == 'burst':
            intensity = level if (i % 10) < 2 else 0
        elif pattern == 'step':
            step_size = steps // 5
            intensity = level * ((i // step_size + 1) / 5.0)
        else:
            intensity = level

        if motor == 'left':
            set_vibration(0, intensity, 0)
        elif motor == 'right':
            set_vibration(0, 0, intensity)
        else:
            set_vibration(0, intensity, intensity)
        time.sleep(interval)
    stop_vibration()

RUMBLE_MAP = {
    "kick": {"notes": range(35, 37), "pattern": "burst", "motor": "left"},
    "snare": {"notes": range(38, 41), "pattern": "pulse", "motor": "right"},
    "hi_hat": {"notes": range(42, 45), "pattern": "fade", "motor": "right"},
    "tom": {"notes": range(47, 50), "pattern": "step", "motor": "left"},
    "cymbal": {"notes": range(49, 52), "pattern": "sine", "motor": "right"},
    "piano_high": {"notes": range(60, 72), "pattern": "sine", "motor": "right"},
    "piano_low": {"notes": range(48, 60), "pattern": "fade", "motor": "left"},
    "default": {"pattern": "constant", "motor": "both"}
}

def get_rumble_settings(note):
    for instrument, config in RUMBLE_MAP.items():
        if note in config.get("notes", []):
            return config["pattern"], config["motor"]
    return RUMBLE_MAP["default"]["pattern"], RUMBLE_MAP["default"]["motor"]

def playback(midi_file, stop_event, rumble_type='fade', play_audio=False):
    mid = mido.MidiFile(midi_file)
    current_time = time.time()

    if play_audio:
        pygame.midi.init()
        pygame.mixer.init()
        try:
            pygame.mixer.music.load(midi_file)
            pygame.mixer.music.play()
        except Exception as e:
            print("Audio playback error:", e)

    for msg in mid:
        if stop_event.is_set():
            break

        current_time += msg.time
        while time.time() < current_time:
            time.sleep(0.001)

        if msg.type == 'note_on' and msg.velocity > 0:
            level = msg.velocity / 127.0
            duration = 0.1
            pattern, motor = get_rumble_settings(msg.note)
            threading.Thread(target=rumble_pattern, args=(pattern, level, duration, motor), daemon=True).start()

    stop_vibration()
    if play_audio:
        pygame.mixer.music.stop()
        pygame.quit()

class VibrationGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MIDI to Controller HD Rumble")
        self.file_path = None
        self.stop_event = threading.Event()
        self.play_thread = None

        self.play_audio = tk.BooleanVar()

        self.file_label = tk.Label(self, text="No file selected")
        self.select_button = tk.Button(self, text="Select MIDI File", command=self.select_file)
        self.play_button = tk.Button(self, text="Play", command=self.start_playback)
        self.stop_button = tk.Button(self, text="Stop", command=self.stop_playback, state=tk.DISABLED)

        self.audio_check = tk.Checkbutton(self, text="Play MIDI Audio", variable=self.play_audio)

        self.file_label.pack(pady=5)
        self.select_button.pack(pady=5)
        self.audio_check.pack()
        self.play_button.pack(pady=5)
        self.stop_button.pack(pady=5)

    def select_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid")])
        if self.file_path:
            self.file_label.config(text=self.file_path.split('/')[-1])

    def start_playback(self):
        if self.file_path and not self.play_thread:
            self.stop_event.clear()
            self.play_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.play_thread = threading.Thread(target=self.playback_thread)
            self.play_thread.start()

    def stop_playback(self):
        self.stop_event.set()

    def playback_thread(self):
        try:
            playback(self.file_path, self.stop_event, play_audio=self.play_audio.get())
        finally:
            self.after(0, self.playback_finished)

    def playback_finished(self):
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.play_thread = None

if __name__ == "__main__":
    app = VibrationGUI()
    app.mainloop()
