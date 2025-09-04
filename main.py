# GestureShot: A Hand Gesture-Based Screenshot Tool
#
# This script uses a webcam to track hand gestures, allowing a user to
# select a region on the screen and capture it in a modern, widget-like GUI.
#
# Acknowledgment:
# Inspired by the hand gesture filtering project by Harsh Kakadiya.
# Original Project: https://github.com/harsh-kakadiya1/computer-vision/tree/main/Vision-Gestures
#
import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import os
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# --- CONFIGURATION ---
SCREENSHOTS_DIR = "screenshots"
EDGE_MARGIN = 0.08
SMOOTHING_FACTOR = 0.2
CAPTURE_COUNTDOWN_SECONDS = 3
SCREENSHOT_COOLDOWN = 3
PREVIEW_WIDTH = 480  # The width of the preview panel in the GUI
UI_TRANSPARENCY = 0.85  # Window transparency (0.0=invisible, 1.0=opaque)


class GestureShotApp:
    """
    The main class for the GestureShot application, encapsulating the GUI,
    camera handling, and gesture recognition logic.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("GestureShot")
        self.root.configure(bg='#2e2e2e')
        self.root.resizable(False, False)
        # Make the window semi-transparent to solve the preview "mirror" effect
        self.root.attributes('-alpha', UI_TRANSPARENCY)

        # --- INITIALIZE STATE VARIABLES ---
        self.smoothed_coords = None
        self.is_capture_mode = False
        self.countdown_start_time = 0
        self.locked_region = None
        self.last_screenshot_time = 0
        self.saved_message_end_time = 0

        # --- SETUP DIRECTORY ---
        if not os.path.exists(SCREENSHOTS_DIR):
            os.makedirs(SCREENSHOTS_DIR)

        # --- INITIALIZE MEDIAPIPE & OPENCV ---
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, max_num_hands=2,
            min_detection_confidence=0.7, min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            return

        ret, frame = self.cap.read()
        if not ret:
            print("Error: Could not read frame from webcam.")
            self.cap.release()
            return

        self.WEBCAM_HEIGHT, self.WEBCAM_WIDTH, _ = frame.shape
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = pyautogui.size()

        # --- SETUP TKINTER GUI ---
        self.setup_gui()

        # --- POSITION WINDOW IN TOP-RIGHT CORNER (after a delay) ---
        # This delay ensures the window is fully rendered before calculating its size.
        self.root.after(100, self.position_window)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_frame()

    def setup_gui(self):
        """Creates the Tkinter widgets for the application."""
        style = ttk.Style()
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="white", font=('Helvetica', 10))

        main_frame = ttk.Frame(self.root, padding="10 10 10 10", style="TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Webcam Feed
        ttk.Label(main_frame, text="Camera").grid(column=0, row=0, pady=5)
        self.webcam_label = ttk.Label(main_frame)
        self.webcam_label.grid(column=0, row=1, padx=5)

        # Screen Preview
        ttk.Label(main_frame, text="Preview").grid(column=1, row=0, pady=5)
        self.preview_label = ttk.Label(main_frame)
        self.preview_label.grid(column=1, row=1, padx=5)

        placeholder = Image.new('RGB', (PREVIEW_WIDTH, int(PREVIEW_WIDTH * (self.WEBCAM_HEIGHT / self.WEBCAM_WIDTH))), (46, 46, 46))
        self.placeholder_img = ImageTk.PhotoImage(image=placeholder)

    def position_window(self):
        """Calculates and sets the window's position to the top-right of the screen."""
        self.root.update_idletasks()
        window_width = self.root.winfo_width()
        x_position = self.SCREEN_WIDTH - window_width
        self.root.geometry(f"+{x_position}+0")

    def on_closing(self):
        """Handles cleanup when the application window is closed."""
        print("Closing application...")
        self.cap.release()
        self.hands.close()
        self.root.destroy()

    def update_frame(self):
        """The main application loop, called repeatedly to update the GUI."""
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(15, self.update_frame)
            return

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        left_hand_landmarks, right_hand_landmarks = None, None
        if results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                self.mp_drawing.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                label = results.multi_handedness[hand_idx].classification[0].label
                if label == "Left":
                    left_hand_landmarks = hand_landmarks
                else:
                    right_hand_landmarks = hand_landmarks

        preview_img = None
        if left_hand_landmarks and right_hand_landmarks:
            frame, preview_img = self.handle_gesture_logic(frame, left_hand_landmarks, right_hand_landmarks)
        else:
            self.smoothed_coords = None
            self.is_capture_mode = False
            self.draw_text(frame, "Show both hands to start", (10, 50), color=(0, 0, 255))

        # Show "Saved!" message if a screenshot was recently taken.
        if time.time() < self.saved_message_end_time:
            self.draw_text(frame, "Saved!", (self.WEBCAM_WIDTH // 2 - 100, self.WEBCAM_HEIGHT // 2), color=(0, 255, 0), font_scale=2)

        # Convert final processed frame to a Tkinter-compatible image.
        webcam_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        webcam_photo = ImageTk.PhotoImage(image=webcam_img)
        self.webcam_label.configure(image=webcam_photo)
        self.webcam_label.image = webcam_photo

        if preview_img is not None:
            preview_photo = ImageTk.PhotoImage(image=preview_img)
            self.preview_label.configure(image=preview_photo)
            self.preview_label.image = preview_photo
        else:
            self.preview_label.configure(image=self.placeholder_img)
            self.preview_label.image = self.placeholder_img

        self.root.after(15, self.update_frame)

    def handle_gesture_logic(self, frame, left_hand_landmarks, right_hand_landmarks):
        """Contains all the logic for gesture detection, selection, and capture."""
        points = [
            left_hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
            right_hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
            right_hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP],
            left_hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        ]

        is_snapped, raw_coords = self.apply_edge_snapping(points)
        self.smooth_coordinates(raw_coords)

        sx1, sy1, sx2, sy2 = [int(c) for c in self.smoothed_coords]
        s_width, s_height = self.clamp_coordinates(sx1, sy1, sx2 - sx1, sy2 - sy1)

        is_trigger_gesture = self.is_pinky_up(left_hand_landmarks) or self.is_pinky_up(right_hand_landmarks)
        frame = self.handle_capture_mode(frame, is_trigger_gesture, (sx1, sy1, s_width, s_height))

        frame = self.draw_visual_feedback(frame, points, is_snapped)

        preview_img = None
        if s_width > 0 and s_height > 0:
            try:
                preview_pil = pyautogui.screenshot(region=(sx1, sy1, s_width, s_height))
                aspect_ratio = s_height / s_width if s_width > 0 else 1
                display_h = int(PREVIEW_WIDTH * aspect_ratio)
                preview_img = preview_pil.resize((PREVIEW_WIDTH, display_h), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"Could not create preview: {e}")

        return frame, preview_img

    def handle_capture_mode(self, frame, is_trigger_gesture, region):
        """Manages the countdown and screenshotting process."""
        if not self.is_capture_mode:
            if is_trigger_gesture:
                self.is_capture_mode = True
                self.countdown_start_time = time.time()
                self.locked_region = region
        else:  # In capture mode
            if not is_trigger_gesture:
                self.is_capture_mode = False

            time_left = CAPTURE_COUNTDOWN_SECONDS - (time.time() - self.countdown_start_time)
            if time_left > 0:
                self.draw_text(frame, str(int(time_left) + 1), (self.WEBCAM_WIDTH // 2 - 30, self.WEBCAM_HEIGHT // 2 + 30), font_scale=3, color=(255, 255, 0))
            else:
                if time.time() - self.last_screenshot_time > SCREENSHOT_COOLDOWN:
                    self.last_screenshot_time = time.time()
                    try:
                        self.root.withdraw()  # Hide window before screenshot
                        screenshot = pyautogui.screenshot(region=self.locked_region)
                        self.root.deiconify()  # Show window again immediately

                        filename = os.path.join(SCREENSHOTS_DIR, f"GestureShot_{time.strftime('%Y%m%d-%H%M%S')}.png")
                        screenshot.save(filename)
                        self.saved_message_end_time = time.time() + 2  # Show "Saved!" for 2 seconds
                    except Exception as e:
                        print(f"Error taking screenshot: {e}")
                        if self.root.state() == 'withdrawn':  # Ensure window reappears on error
                            self.root.deiconify()
                self.is_capture_mode = False
        return frame

    def draw_visual_feedback(self, frame, points, is_snapped):
        """Draws the selection rectangle and text overlays on the webcam frame."""
        rect_color = (0, 255, 0)  # Green: Framing
        if is_snapped and not self.is_capture_mode: rect_color = (255, 0, 0)  # Blue: Snapped
        if self.is_capture_mode: rect_color = (0, 255, 255)  # Yellow: Locked-in

        frame_x1 = int(min(p.x for p in points) * self.WEBCAM_WIDTH)
        frame_y1 = int(min(p.y for p in points) * self.WEBCAM_HEIGHT)
        frame_x2 = int(max(p.x for p in points) * self.WEBCAM_WIDTH)
        frame_y2 = int(max(p.y for p in points) * self.WEBCAM_HEIGHT)

        overlay = frame.copy()
        cv2.rectangle(overlay, (frame_x1, frame_y1), (frame_x2, frame_y2), rect_color, -1)
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
        cv2.rectangle(frame, (frame_x1, frame_y1), (frame_x2, frame_y2), rect_color, 2)
        self.draw_text(frame, "Raise a pinky to capture", (10, 50), color=(0, 255, 255))
        return frame

    # --- HELPER FUNCTIONS ---
    def apply_edge_snapping(self, points):
        is_snapped = False
        raw_coords = []
        for p in points:
            nx, ny = p.x, p.y
            if nx < EDGE_MARGIN:
                nx = 0.0; is_snapped = True
            elif nx > 1 - EDGE_MARGIN:
                nx = 1.0; is_snapped = True
            if ny < EDGE_MARGIN:
                ny = 0.0; is_snapped = True
            elif ny > 1 - EDGE_MARGIN:
                ny = 1.0; is_snapped = True
            raw_coords.append((nx * self.SCREEN_WIDTH, ny * self.SCREEN_HEIGHT))
        return is_snapped, raw_coords

    def smooth_coordinates(self, raw_coords):
        current_box = (min(c[0] for c in raw_coords), min(c[1] for c in raw_coords),
                       max(c[0] for c in raw_coords), max(c[1] for c in raw_coords))
        if self.smoothed_coords is None:
            self.smoothed_coords = current_box
        else:
            self.smoothed_coords = tuple(
                (SMOOTHING_FACTOR * current) + ((1 - SMOOTHING_FACTOR) * smoothed)
                for current, smoothed in zip(current_box, self.smoothed_coords)
            )

    def clamp_coordinates(self, x, y, w, h):
        x = max(0, x)
        y = max(0, y)
        w = min(self.SCREEN_WIDTH - x, w)
        h = min(self.SCREEN_HEIGHT - y, h)
        return w, h

    def draw_text(self, frame, text, position, color=(255, 255, 255), font_scale=1, thickness=2):
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 3)
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

    def is_pinky_up(self, hand_landmarks):
        if not hand_landmarks: return False
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        pinky_mcp = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_MCP]
        return pinky_tip.y < pinky_mcp.y


if __name__ == "__main__":
    root = tk.Tk()
    app = GestureShotApp(root)
    root.mainloop()

