# GestureShot 📸

Take screenshots of specific screen regions by framing the area with your hands and pinching your fingers!

GestureShot uses your webcam to track your hand movements, mapping them to your screen. Define a rectangular area using your thumbs and index fingers, and pinch with one hand to instantly capture and save that selection.

---

## Features

-   **Intuitive Control:** Use natural hand gestures to select and capture screen regions.
-   **Real-time Feedback:** A live webcam preview shows your hand tracking and the currently selected area.
-   **Precise Selection:** Frame the exact portion of the screen you need.
-   **Single-Pinch Trigger:** A simple pinch gesture with either your left or right hand is all it takes to capture.

## How It Works

The application maps the coordinates of your hands from the webcam's view to your entire screen.

1.  **Hand Tracking:** It uses the MediaPipe library to detect the landmarks of your thumbs and index fingers on both hands.
2.  **Coordinate Mapping:** The positions of these four landmarks on the webcam feed are scaled up to your screen's full resolution.
3.  **Area Definition:** The mapped points of your fingers define the corners of the rectangular area to be captured.
4.  **Capture Trigger:** When you pinch the thumb and index finger of a *single* hand together, the application takes a screenshot of the entire screen and then crops it down to your selected area.
5.  **Saving:** The final cropped image is saved to a local `screenshots` directory.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/GestureShot.git](https://github.com/YOUR_USERNAME/GestureShot.git)
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

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Make sure your webcam is connected and uncovered.
2.  Run the main script from the terminal:
    ```bash
    python main.py
    ```
3.  An OpenCV window will appear showing your webcam feed.
4.  Hold both hands up in front of the camera to define the screenshot area with your thumbs and index fingers.
5.  Pinch the thumb and index finger of *either* your left or right hand together to take the screenshot.
6.  The captured image will be saved in the `screenshots` folder.
7.  Press the 'q' key to close the application.

## Acknowledgements

This project was inspired by and builds upon the hand gesture filtering concept from **Harsh Kakadiya**. A big thank you for sharing the foundational code and idea.

-   **Original Project:** [Vision-Gestures](https://github.com/harsh-kakadiya1/computer-vision/tree/main/Vision-Gestures)
-   **Original Author:** [Harsh Kakadiya](https://github.com/harsh-kakadiya1)
