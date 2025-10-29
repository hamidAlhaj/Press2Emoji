import os
import json
import tkinter as tk
from PIL import Image, ImageTk
import keyboard  # pip install keyboard

# CONFIG
BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
WINDOW_W = 1280
WINDOW_H = 720
DISPLAY_TIME_MS = 5000  # 5000 ms = 5 seconds

# Load config
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

# read default image path if present
DEFAULT_IMAGE_PATH = CONFIG.get("_default", {}).get("image")

class KeyImageOverlay:
    def __init__(self, root):
        self.root = root
        self.root.title("Key -> Image Overlay")
        self.root.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.root.attributes("-topmost", True)
        # self.root.overrideredirect(True)  # uncomment for borderless

        self.canvas = tk.Canvas(root, width=WINDOW_W, height=WINDOW_H)
        self.canvas.pack(fill="both", expand=True)

        # Preload images
        self.loaded = {}
        for key, info in CONFIG.items():
            if key == "_default":
                continue
            img_path = os.path.join(BASE_DIR, info["image"])
            try:
                from PIL import Image as PILImage
                im = PILImage.open(img_path).resize((WINDOW_W, WINDOW_H), PILImage.LANCZOS)
                self.loaded[key] = ImageTk.PhotoImage(im)
            except Exception as e:
                print(f"Failed to load {img_path}: {e}")

        # load default image if exists
        self.default_imgtk = None
        if DEFAULT_IMAGE_PATH:
            try:
                from PIL import Image as PILImage
                dpath = os.path.join(BASE_DIR, DEFAULT_IMAGE_PATH)
                dim = PILImage.open(dpath).resize((WINDOW_W, WINDOW_H), PILImage.LANCZOS)
                self.default_imgtk = ImageTk.PhotoImage(dim)
            except Exception as e:
                print(f"Failed to load default image {DEFAULT_IMAGE_PATH}: {e}")

        self.image_id = None
        self.current_timer = None  # store after() id to cancel if needed

        # show default image initially (if available)
        if self.default_imgtk:
            self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.default_imgtk)
            self.canvas.image = self.default_imgtk

        # Bind keys (keyboard library listens globally)
        for k in CONFIG.keys():
            if k == "_default": 
                continue
            try:
                keyboard.on_press_key(k, lambda e, key=k: self.on_key_press(key))
            except Exception as ex:
                print("keyboard listener error:", ex)

        # allow quitting with ESC
        keyboard.on_press_key("esc", lambda e: self.quit())

    def on_key_press(self, key):
        # cancel previous timer if running
        if self.current_timer is not None:
            try:
                self.root.after_cancel(self.current_timer)
            except Exception:
                pass
            self.current_timer = None

        # show the key image (if loaded)
        imgtk = self.loaded.get(key)
        if imgtk:
            if self.image_id:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=imgtk)
            self.canvas.image = imgtk

        # schedule return to default after DISPLAY_TIME_MS
        if self.default_imgtk:
            self.current_timer = self.root.after(DISPLAY_TIME_MS, self.show_default)
        else:
            # if no default image, we can clear after time
            self.current_timer = self.root.after(DISPLAY_TIME_MS, self.clear_image)

    def show_default(self):
        # show default image (if available)
        if self.default_imgtk:
            if self.image_id:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.default_imgtk)
            self.canvas.image = self.default_imgtk
        self.current_timer = None

    def clear_image(self):
        if self.image_id:
            self.canvas.delete(self.image_id)
            self.image_id = None
        self.current_timer = None

    def quit(self):
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self.root.quit()

def start_tk():
    root = tk.Tk()
    app = KeyImageOverlay(root)
    root.mainloop()

if __name__ == "__main__":
    start_tk()
