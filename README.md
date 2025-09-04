# GestureShot: A Gesture-Controlled Screenshot Tool

GestureShot is a modern, Python-based application that allows you to capture screenshots using hand gestures. By tracking your hands through your webcam, you can intuitively select a region of your screen and save it as an image, all without ever touching your mouse or keyboard.

The application runs in a sleek, semi-transparent, widget-like window that docks in the top-right corner of your screen, providing a seamless and non-intrusive user experience.



---

## Key Features

- **Intuitive Gesture Control:** Use your thumbs and index fingers on both hands to create and position the selection frame.
- **Stable Trigger Mechanism:** Simply raise the pinky of either hand to lock the frame and start a 3-second capture countdown. Lowering the pinky cancels the countdown.
- **Modern GUI:** A unified, semi-transparent window built with Tkinter shows both the live camera feed and the screen preview side-by-side.
- **Clean Screenshots:** The application window automatically hides itself for a fraction of a second during capture, ensuring it never appears in the final screenshot.
- **Live Preview:** See exactly what you're about to capture in a real-time preview panel.
- **Jitter-Free Selection:** Coordinate smoothing is applied to hand movements, resulting in a stable and precise selection box.
- **Edge Snapping:** Easily select the full width or height of your screen by moving your hands to the edges.

---

## Requirements

The application is built with Python and requires the following libraries:

- `opencv-python`
- `mediapipe`
- `numpy`
- `pyautogui`
- `Pillow`

You can install all dependencies at once using the provided `requirements.txt` file.

---

## Installation & Usage

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/GestureShot.git](https://github.com/your-username/GestureShot.git)
    cd GestureShot
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\\venv\\Scripts\\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python GestureShot.py
    ```

---

## How to Use

1.  Launch the application. The UI will appear in the top-right corner of your screen.
2.  Hold both hands up in front of your webcam. A semi-transparent rectangle will appear on your webcam feed, representing the selection area.
3.  Move your hands to position and resize the selection. The live preview panel will show you what's inside the capture region.
4.  Once you are happy with the selection, hold your hands steady and **raise the pinky finger** of either your left or right hand.
5.  A countdown will begin. To cancel, simply lower your pinky.
6.  Upon completion, the screenshot will be saved to the `screenshots/` directory in the project folder.

---

## Acknowledgment

This project was inspired by and builds upon the concepts demonstrated in a hand gesture filtering project by **Harsh Kakadiya**.

-   **Original Project:** [Vision-Gestures on GitHub](https://github.com/harsh-kakadiya1/computer-vision/tree/main/Vision-Gestures)