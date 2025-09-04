# GestureShot: The Hand-Waving Screenshot & Annotation Tool!

Ever felt that pressing `PrtScn` is just... so last century? Welcome to GestureShot, a Python application that lets you command your screen with the power of your own two hands. Frame a region, snap a screenshot, summon it back, and doodle on it like you're in a sci-fi movie.

The application runs as a sleek, always-on-top widget, making it a seamless part of your desktop workflow. It's basically magic, but with more Python.


---

### Key Features

- **✨ Summon & Annotate:** Use a "come here" gesture to magically summon your last screenshot. Draw on it with your fist, save it with a thumbs-up, or banish it with an open palm.
- **🧠 Extensible Modular Architecture:** The app is now built on a core engine with pluggable "extensions." Got an idea for a new gesture? You can build it! (See "Contributing" below).
- **🖥️ Sleek Desktop Widget:** The main UI is now a borderless, semi-transparent, always-on-top window that docks neatly in the corner of your screen. It's there when you need it, and unobtrusive when you don't.
- **🖐️ Intuitive Gesture Controls:** The gestures are designed to be robust and reliable. **Hold a gesture** for a moment to confirm an action, preventing accidental clicks and rage-quits.
- **🎯 Jitter-Free Precision:** All hand movements, from selecting to drawing, are smoothed to filter out camera shake, giving you surprisingly fine control.
- **🖼️ Live Preview:** See exactly what you're about to capture or summon in a real-time preview panel. No more guessing games.

---

### How to Use: Your Gesture Spellbook

Ready to wave your hands like you just don't care? Here's how.

#### 📸 The Classic Screenshot

1.  **Show Two Hands:** Present both hands to the camera. This activates screenshot mode.
2.  **Frame It:** Use your index fingers and thumbs to form a rectangle. This is your capture area.
3.  **Lock & Capture:** Raise a **pinky finger** to lock in the selection and start the 3-second countdown. A screenshot is saved to the `screenshots/` folder.

#### 🎨 The Annotation Wizard

1.  **First, Take a Screenshot:** You need something to summon, after all!
2.  **Summon Your Creation:** Show **one hand** and perform a "come here" motion with your index finger. Your last screenshot will appear in a new window.
3.  **Control the Magic Wand:**
    * **Move Cursor (Blue):** Use a neutral, open hand.
    * **Draw (Red):** Make a **tight fist** and move your hand to draw on the image.
    * **Save & Close:** Give a clear **👍 Thumbs-Up** and hold it for a second. Your masterpiece is saved to the `annotated/` folder.
    * **Close Without Saving:** Show a flat **✋ Open Palm** ("stop!") and hold it for a second. The window vanishes.

---

### Become a Gesture Wizard: Contributing

Got an idea for a gesture that mutes your Zoom call or orders a pizza? This project is built for it. The new architecture separates the core "engine" from the "extensions" that provide the actual functionality.

**The Gist:** You can easily write your own extension without touching the core camera or UI code!

An extension is just a Python class that inherits from `GestureExtension` and implements a few key methods:

-   `check_for_activation(...)`: Is the specific gesture for *your* feature happening right now? (e.g., "Are two hands visible?"). If yes, return `True`.
-   `process_gestures(...)`: Your extension is now active! This method runs every frame. Here, you'll check for other gestures (like "is the pinky up?") and perform actions.
-   `draw_feedback(...)`: Draw helpful guides or text on the main camera feed so the user knows what's happening.

Here's a sneak peek at the structure:
```python
from .base_extension import GestureExtension

class YourCoolExtension(GestureExtension):
    def check_for_activation(self, results, frame):
        # Return True if your starting gesture is detected
        pass

    def process_gestures(self, results, frame):
        # Your main logic goes here when the extension is active
        # Don't forget to release control when you're done!
        # self.app.release_active_extension()
        pass

    def draw_feedback(self, frame):
        # Draw something cool on the frame
        return frame, None # frame, preview_image
```
Fork the repo, create your extension in the `/extensions` folder, add it to `main.py`, and submit a pull request. We'd love to see what you build!

---

### Requirements

The application is built with Python and requires the following libraries:

- `opencv-python`
- `mediapipe`
- `numpy`
- `pyautogui`
- `Pillow`

### Installation & Usage

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/spheppner/gestureshot.git
    cd gestureshot
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows: .\venv\Scripts\activate
    # On macOS/Linux: source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python main.py
    ```

---

### Acknowledgment

This project was inspired by and builds upon the concepts demonstrated in a hand gesture filtering project by **Harsh Kakadiya**.

-   **Original Project:** [Vision-Gestures on GitHub](https://github.com/harsh-kakadiya1/computer-vision/tree/main/Vision-Gestures)