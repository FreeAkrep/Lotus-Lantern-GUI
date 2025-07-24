# 🌸 Lotus Lantern

A modern Python desktop app to control BLE LED strips wirelessly.  
Simple, dark-themed UI with system tray support, persistent settings, and effect previews.  
Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) and [Bleak](https://github.com/hbldh/bleak).

![UI Screenshot](https://github.com/FreeAkrep/Lotus-Lantern-win/blob/main/screenshots/ui_main.png?raw=true)

---

## ✨ Features

- 🔌 Connect to BLE-enabled LED controllers
- 🎨 Change LED colors with color picker or tray presets
- 💡 Adjust brightness (scaled 1–5)
- 🎭 Switch between lighting modes: Static, Fade, Blink, Rainbow, Strobe, Wave
- ⚡ Adjust effect speed
- 💾 Remembers last settings on next launch
- 🧲 Minimize to system tray with full tray control
- 🔧 Simple JSON-based config

---

## 📦 Installation (Windows)

### Option 1: Run from Source (Recommended)

1. Install Python 3.10+  
2. Clone this repo:

```bash
git clone https://github.com/FreeAkrep/Lotus-Lantern-win
cd Lotus-Lantern-win
pip install -r requirements.txt
python main.py

