import asyncio
import customtkinter as ctk
from bleak import BleakClient, BleakScanner
from threading import Thread
from tkinter import colorchooser, messagebox
import json
import os
import itertools

from src.ble_commands import (
    send_turn_on, send_turn_off,
    send_color, send_brightness,
    send_mode, send_effect_speed
)

CONFIG_PATH = "config.json"
ICON_PATH = "icon.ico"
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class BLEApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lotus Lantern")
        self.geometry("400x520")
        self.resizable(False, False)

        self.devices = []
        self.client = None
        self.current_color = (0, 255, 0)
        self.current_brightness = 128
        self.saved_mode = "Static"
        self.saved_speed = 50

        self.load_settings()
        self.create_scan_ui()
        Thread(target=self.run_loop, daemon=True).start()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def run_loop(self):
        loop.run_forever()

    def create_scan_ui(self):
        self.clear_window()

        ctk.CTkLabel(self, text="BLE Light Control", font=("Arial", 18)).pack(pady=(15, 5))

        self.scan_btn = ctk.CTkButton(self, text="\U0001f504 SCAN", command=self.scan_devices)
        self.scan_btn.pack(pady=10)

        self.device_menu = ctk.CTkOptionMenu(self, values=["No Devices"], command=self.device_selected)
        self.device_menu.pack(pady=10)

        self.connect_btn = ctk.CTkButton(self, text="CONNECT", state="disabled", command=self.connect_device)
        self.connect_btn.pack(pady=10)

    def create_control_ui(self):
        self.clear_window()

        ctk.CTkButton(self, text="DISCONNECT", fg_color="#9b5de5", command=self.disconnect_device).pack(pady=(15, 10))

        power_frame = ctk.CTkFrame(self)
        power_frame.pack(pady=5)
        ctk.CTkButton(power_frame, text="ON", command=self.send_turn_on).pack(side="left", padx=5)
        ctk.CTkButton(power_frame, text="OFF", command=self.send_turn_off).pack(side="left", padx=5)

        ctk.CTkLabel(self, text="Pick Color").pack(pady=(10, 3))
        self.color_preview = ctk.CTkLabel(self, text="", width=100, height=25, corner_radius=8)
        self.color_preview.pack()
        self.update_color_preview()
        ctk.CTkButton(self, text="Choose Color", command=self.choose_color).pack(pady=5)

        ctk.CTkLabel(self, text="Brightness").pack(pady=(10, 3))
        self.brightness_slider = ctk.CTkSlider(self, from_=0, to=255, number_of_steps=255, command=self.change_brightness)
        self.brightness_slider.set(self.current_brightness)
        self.brightness_slider.pack(pady=5)

        ctk.CTkLabel(self, text="Light Mode").pack(pady=(10, 3))
        self.mode_menu = ctk.CTkOptionMenu(self,
            values=["Static", "Fade", "Blink", "Rainbow", "Strobe", "Wave"],
            command=self.set_mode)
        self.mode_menu.pack(pady=5)
        self.mode_menu.set(self.saved_mode)

        ctk.CTkLabel(self, text="Effect Speed").pack(pady=(10, 3))
        self.effect_speed_slider = ctk.CTkSlider(self, from_=1, to=100, command=self.change_effect_speed)
        self.effect_speed_slider.set(self.saved_speed)
        self.effect_speed_slider.pack(pady=5)

        self.effect_preview = ctk.CTkLabel(self, text="Preview", width=120, height=30, corner_radius=10)
        self.effect_preview.pack(pady=(10, 5))
        self.animate_preview(self.mode_menu.get())

    def scan_devices(self):
        self.device_menu.configure(values=["Scanning..."])
        asyncio.run_coroutine_threadsafe(self.scan_async(), loop)

    async def scan_async(self):
        self.devices = await BleakScanner.discover()
        names = [d.name or d.address for d in self.devices]
        if not names:
            names = ["No Devices Found"]
        self.device_menu.configure(values=names)
        self.device_menu.set(names[0])
        self.connect_btn.configure(state="normal" if self.devices else "disabled")

    def device_selected(self, _):
        self.connect_btn.configure(state="normal")

    def connect_device(self):
        index = self.device_menu.cget("values").index(self.device_menu.get())
        selected_device = self.devices[index]
        asyncio.run_coroutine_threadsafe(self.connect_async(selected_device), loop)

    async def connect_async(self, device):
        try:
            self.client = BleakClient(device)
            await self.client.connect()
            self.create_control_ui()
        except Exception as e:
            messagebox.showerror("Connection Failed", str(e))

    def disconnect_device(self):
        self.save_settings()
        if hasattr(self, 'effect_preview') and self.effect_preview.winfo_exists():
            self.effect_preview.configure(bg_color="#222222")
        if self.client:
            asyncio.run_coroutine_threadsafe(self.client.disconnect(), loop)
        self.client = None
        self.create_scan_ui()

    def send_turn_on(self):
        if self.client:
            asyncio.run_coroutine_threadsafe(send_turn_on(self.client), loop)

    def send_turn_off(self):
        if self.client:
            asyncio.run_coroutine_threadsafe(send_turn_off(self.client), loop)

    def choose_color(self):
        color = colorchooser.askcolor()[0]
        if color:
            self.current_color = tuple(int(c) for c in color)
            self.update_color_preview()
            if self.client:
                asyncio.run_coroutine_threadsafe(send_color(self.client, self.current_color), loop)

    def update_color_preview(self):
        hex_color = self.rgb_to_hex(self.current_color)
        self.color_preview.configure(bg_color=hex_color)

    def change_brightness(self, value):
        self.current_brightness = int(value)
        if self.client:
            asyncio.run_coroutine_threadsafe(send_brightness(self.client, self.current_brightness), loop)

    def change_effect_speed(self, value):
        if self.client:
            asyncio.run_coroutine_threadsafe(send_effect_speed(self.client, int(value)), loop)

    def set_mode(self, mode):
        if self.client and self.client.is_connected:
            asyncio.run_coroutine_threadsafe(self.set_light_mode(mode), loop)
        self.animate_preview(mode)

    async def set_light_mode(self, mode):
        try:
            await send_mode(self.client, mode)
            messagebox.showinfo("Success", f"Mode set to: {mode}")
        except Exception as e:
            messagebox.showerror("Error setting mode", str(e))

    def animate_preview(self, mode):
        colors = {
            "Fade": ["#ff0000", "#00ff00", "#0000ff"],
            "Blink": ["#ffffff", "#000000"],
            "Rainbow": ["#ff0000", "#ff7f00", "#ffff00", "#00ff00", "#0000ff", "#4b0082", "#8f00ff"],
            "Strobe": ["#ffffff", "#000000"],
            "Wave": ["#00ffff", "#0000ff", "#ff00ff"],
            "Static": [self.rgb_to_hex(self.current_color)],
        }.get(mode, ["#111111"])

        self._preview_cycle = itertools.cycle(colors)

        def step():
            try:
                next_color = next(self._preview_cycle)
                if self.effect_preview.winfo_exists():
                    self.effect_preview.configure(bg_color=next_color)
                    self.after(300, step)
            except Exception:
                pass

        step()

    def rgb_to_hex(self, rgb):
        return "#%02x%02x%02x" % rgb

    def save_settings(self):
        config = {
            "color": self.current_color,
            "brightness": self.current_brightness,
            "mode": self.mode_menu.get(),
            "effect_speed": self.effect_speed_slider.get()
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)

    def load_settings(self):
        if not os.path.exists(CONFIG_PATH):
            return
        with open(CONFIG_PATH, "r") as f:
            try:
                config = json.load(f)
                self.current_color = tuple(config.get("color", (0, 255, 0)))
                self.current_brightness = config.get("brightness", 128)
                self.saved_mode = config.get("mode", "Static")
                self.saved_speed = config.get("effect_speed", 50)
            except Exception:
                pass


if __name__ == "__main__":
    app = BLEApp()
    app.mainloop()
