import tkinter as tk
import os
from gesture_app_base import GestureAppBase
from extensions.screenshot_ext import ScreenshotExtension
from extensions.annotation_ext import AnnotationExtension

if __name__ == "__main__":
    # --- Create necessary directories ---
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
    if not os.path.exists("annotated"):
        os.makedirs("annotated")

    root = tk.Tk()
    app = GestureAppBase(root)

    # --- Load the desired functionalities as extensions ---
    # The order doesn't matter. The app will poll each one.
    app.load_extensions(
        ScreenshotExtension,
        AnnotationExtension
    )

    root.mainloop()
