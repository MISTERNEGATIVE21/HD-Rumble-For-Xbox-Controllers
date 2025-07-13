import tkinter as tk
from tkinter import filedialog
import threading
import time
import ctypes
import mido

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
    """Set vibration levels for the controller motors."""
    vibration = XINPUT_VIBRATION(int(left * 65535), int(right * 65535))
    XInputSetState(controller, ctypes.byref(vibration))

def emulate_hd_rumble(level, duration, motor='both'):
    """
    Simulate HD rumble effect for a short time with vibration modulation.
    """
    interval = 0.01  # 10 ms step
    steps = int(duration / interval)
    for i in range(steps):
        if steps == 0:
            break
        factor = 1.0 - (i / steps)  # Linear decay
        intensity = level * factor
        if motor == 'left':
            set_vibration(0, intensity, 0)
        elif motor == 'right':
            set_vibration(0, 0, intensity)
        else:
            set_vibration(0, intensity, intensity)
        time.sleep(interval)
    set_vibration(0, 0, 0)

def playback(midi_file, stop_event):
    """Process MIDI file and play vibrations with simulated HD rumble."""
    mid = mido.MidiFile(midi_file)
    current_time = time.time()
    threshold = 60  # Middle C

    for msg in mid:
        if stop_event.is_set():
            break

        current_time += msg.time
        while time.time() < current_time:
            time.sleep(0.001)

        if msg.type == 'note_on' and msg.velocity > 0:
            level = msg.velocity / 127.0
            duration = 0.1  # 100 ms
            motor = 'left' if msg.note < threshold else 'right'
            threading.Thread(target=emulate_hd_rumble, args=(level, duration, motor), daemon=True).start()

    set_vibration(0, 0, 0)

class VibrationGUI(tk.Tk):
    def __init__(self):
        """Initialize the GUI window and widgets."""
        super().__init__()
        self.title("MIDI to Controller HD Rumble")
        self.file_path = None
        self.stop_event = threading.Event()
        self.play_thread = None

        # Create GUI elements
        self.file_label = tk.Label(self, text="No file selected")
        self.select_button = tk.Button(self, text="Select MIDI File", command=self.select_file)
        self.play_button = tk.Button(self, text="Play", command=self.start_playback)
        self.stop_button = tk.Button(self, text="Stop", command=self.stop_playback, state=tk.DISABLED)

        # Layout widgets
        self.file_label.pack(pady=5)
        self.select_button.pack(pady=5)
        self.play_button.pack(pady=5)
        self.stop_button.pack(pady=5)

    def select_file(self):
        """Open file dialog to select a MIDI file."""
        self.file_path = filedialog.askopenfilename(filetypes=[("MIDI files", "*.mid")])
        if self.file_path:
            self.file_label.config(text=self.file_path.split('/')[-1])

    def start_playback(self):
        """Start playback in a separate thread."""
        if self.file_path and not self.play_thread:
            self.stop_event.clear()
            self.play_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.play_thread = threading.Thread(target=self.playback_thread)
            self.play_thread.start()

    def stop_playback(self):
        """Signal the playback thread to stop."""
        self.stop_event.set()

    def playback_thread(self):
        """Run the playback function and handle cleanup."""
        try:
            playback(self.file_path, self.stop_event)
        finally:
            self.after(0, self.playback_finished)

    def playback_finished(self):
        """Reset GUI state after playback ends."""
        self.play_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.play_thread = None

if __name__ == "__main__":
    app = VibrationGUI()
    app.mainloop()
