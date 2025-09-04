import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import time
import os


class AnnotationWindow:
    """
    A Toplevel window for displaying and drawing on an image, with
    input smoothing for the cursor.
    """
    ACTION_GRACE_PERIOD = 1.0  # Ignore actions for 1 second after creation
    SMOOTHING_FACTOR = 0.3  # Lower is smoother but has more "drag"

    def __init__(self, parent_root, image_path):
        self.root = tk.Toplevel(parent_root)
        self.root.overrideredirect(True)
        self.root.configure(bg="#1e1e1e")

        # --- State ---
        self.is_closed = False
        self.creation_time = time.time()
        self.image_path = image_path
        self.original_image = Image.open(image_path).convert("RGBA")
        self.display_image = self.original_image.copy()
        self.draw = ImageDraw.Draw(self.display_image)
        self.last_smoothed_pos = None  # Stores previous smoothed position for drawing lines
        self.is_drawing = False
        self.message = ""
        self.message_end_time = 0

        # --- Smoothing State ---
        self.smoothed_cursor_pos = None  # Stores the current smoothed position

        try:
            self.font = ImageFont.truetype("arial.ttf", 30)
        except IOError:
            print("Arial font not found, using default.")
            self.font = ImageFont.load_default()

        # --- Calculate size and position ---
        screen_w = parent_root.winfo_screenwidth()
        screen_h = parent_root.winfo_screenheight()
        max_h = int(screen_h * 0.8)

        img_w, img_h = self.original_image.size
        aspect_ratio = img_w / img_h if img_h > 0 else 1
        new_h = max_h
        new_w = int(new_h * aspect_ratio)

        self.canvas_size = (new_w, new_h)

        # --- Create Widgets ---
        self.canvas = tk.Canvas(self.root, width=new_w, height=new_h, highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        self.tk_image = ImageTk.PhotoImage(self.display_image.resize(self.canvas_size, Image.Resampling.LANCZOS))
        self.canvas_img = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)

        x_pos = (screen_w // 2) - (new_w // 2)
        y_pos = (screen_h // 2) - (new_h // 2)
        self.root.geometry(f"{new_w + 20}x{new_h + 20}+{x_pos}+{y_pos}")

        self.root.focus_force()

        # --- UI CHANGE: Add a custom close button ---
        close_button = tk.Button(self.root, text="✕", command=self.on_manual_close,
                                 bg="#1e1e1e", fg="white", font=("Arial", 12, "bold"),
                                 borderwidth=0, highlightthickness=0, relief="flat",
                                 activebackground="#c0392b", activeforeground="white")
        close_button.place(relx=1.0, x=-5, y=5, anchor="ne")

    def on_manual_close(self):
        self.is_closed = True
        self.root.destroy()

    def update_cursor(self, raw_cursor_pos, is_drawing):
        """Smooths the cursor position and draws if needed."""
        if not self.root.winfo_exists(): return

        # --- Apply Exponential Moving Average for Smoothing ---
        if self.smoothed_cursor_pos is None:
            self.smoothed_cursor_pos = raw_cursor_pos
        else:
            sx = (self.SMOOTHING_FACTOR * raw_cursor_pos[0] +
                  (1 - self.SMOOTHING_FACTOR) * self.smoothed_cursor_pos[0])
            sy = (self.SMOOTHING_FACTOR * raw_cursor_pos[1] +
                  (1 - self.SMOOTHING_FACTOR) * self.smoothed_cursor_pos[1])
            self.smoothed_cursor_pos = (sx, sy)

        if is_drawing and self.last_smoothed_pos:
            # Scale smoothed coordinates to original image size for drawing
            orig_x1 = int(self.last_smoothed_pos[0] * self.original_image.width)
            orig_y1 = int(self.last_smoothed_pos[1] * self.original_image.height)
            orig_x2 = int(self.smoothed_cursor_pos[0] * self.original_image.width)
            orig_y2 = int(self.smoothed_cursor_pos[1] * self.original_image.height)
            self.draw.line([(orig_x1, orig_y1), (orig_x2, orig_y2)], fill="red", width=8)

        self.last_smoothed_pos = self.smoothed_cursor_pos
        self.is_drawing = is_drawing
        self._redraw_canvas()

    def _redraw_canvas(self):
        """Redraws the canvas with the image and smoothed cursor."""
        if not self.root.winfo_exists(): return

        resized_img = self.display_image.resize(self.canvas_size, Image.Resampling.LANCZOS)

        draw_display = ImageDraw.Draw(resized_img)
        if self.smoothed_cursor_pos:
            cx = int(self.smoothed_cursor_pos[0] * self.canvas_size[0])
            cy = int(self.smoothed_cursor_pos[1] * self.canvas_size[1])
            cursor_color = "red" if self.is_drawing else "cyan"
            draw_display.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=cursor_color, outline="black")

        if time.time() < self.message_end_time:
            w, h = resized_img.size
            draw_display.text((w / 2, h - 40), self.message, fill="lime", font=self.font, anchor="ms")

        self.tk_image = ImageTk.PhotoImage(resized_img)
        self.canvas.itemconfig(self.canvas_img, image=self.tk_image)

    def save_and_copy(self):
        """Saves the annotated image, ignoring calls within the grace period."""
        if self.is_closed or time.time() - self.creation_time < self.ACTION_GRACE_PERIOD:
            return

        try:
            if not os.path.exists("annotated"):
                os.makedirs("annotated")
            base = os.path.splitext(os.path.basename(self.image_path))[0]
            filename = os.path.join("annotated", f"{base}_annotated_{time.strftime('%H%M%S')}.png")
            self.display_image.save(filename)
            self.message = "Saved!"
            print(f"Saved to {filename}")
        except Exception as e:
            self.message = f"Error: {e}"
            print(self.message)
        self.message_end_time = time.time() + 2.0
        self._redraw_canvas()
        self.root.after(1000, self.close)

    def close(self):
        """Closes the window, ignoring calls within the grace period."""
        if self.is_closed or time.time() - self.creation_time < self.ACTION_GRACE_PERIOD:
            return
        self.is_closed = True
        self.root.destroy()

