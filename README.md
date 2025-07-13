# HD Rumble for Xbox Controllers

This project brings **HD Rumble-style feedback** to Xbox controllers using MIDI files. It translates MIDI note data into varying vibration patterns—simulating richer tactile feedback like Nintendo Switch’s HD Rumble.

🎵 MIDI note triggers  
🎮 Xbox controller vibration  
🔊 Optional MIDI audio playback  
🪟 Windows GUI interface using Tkinter  

---

## 🧰 Features

- Play MIDI files and feel note-driven vibration
- Custom vibration patterns: `pulse`, `fade`, `sine`, `burst`, `step`, and more
- Left/Right motor mapping for musical instrument zones
- Audio playback option via `pygame` (for syncing vibration with sound)
- Intuitive Tkinter GUI

---

## 📦 Requirements

Install dependencies listed in `req.txt`:

```bash
pip install -r req.txt
