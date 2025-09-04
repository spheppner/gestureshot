# Acknowledgment:
# Inspired by the hand gesture filtering project by Harsh Kakadiya.
# Original Project: https://github.com/harsh-kakadiya1/computer-vision/tree/main/Vision-Gestures

import cv2
import numpy as np
import mediapipe as mp
import pyautogui
from PIL import Image
import os
import time

# --- CONFIGURATION AND INITIALIZATION ---

# 1. Folder to save screenshots
SCREENSHOTS_DIR = "screenshots"
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)

# 2. MediaPipe Hands Initialization
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# 3. Screen and Webcam Setup
# Get screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

# Start webcam capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Get webcam frame dimensions
ret, frame = cap.read()
if not ret:
    print("Error: Could not read frame from webcam.")
    cap.release()
    exit()
WEBCAM_HEIGHT, WEBCAM_WIDTH, _ = frame.shape

# 4. Gesture Control Variables
PINCH_THRESHOLD = 30  # Max distance in pixels between thumb and index for a pinch
SCREENSHOT_COOLDOWN = 3  # Seconds between screenshots
last_screenshot_time = 0


# --- HELPER FUNCTIONS ---

def draw_text(frame, text, position, color=(0, 255, 0), font_scale=1, thickness=2):
    """Draws text with a black outline for better visibility."""
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 2)
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)


# --- MAIN APPLICATION LOOP ---

try:
    preview_window_open = False  # Track the state of the preview window
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Flip the frame horizontally for a mirror effect
        frame = cv2.flip(frame, 1)
        # Create a copy to draw the overlay on
        overlay_frame = frame.copy()

        # Convert the BGR image to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        # Variables to store hand landmarks and pinch status
        left_hand_landmarks = None
        right_hand_landmarks = None
        is_left_pinch = False
        is_right_pinch = False

        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) <= 2:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Draw landmarks on the original frame
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Identify left vs. right hand
                hand_label = results.multi_handedness[hand_idx].classification[0].label

                # Get thumb and index finger tip coordinates
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

                # Convert to pixel coordinates
                x_thumb, y_thumb = int(thumb_tip.x * WEBCAM_WIDTH), int(thumb_tip.y * WEBCAM_HEIGHT)
                x_index, y_index = int(index_tip.x * WEBCAM_WIDTH), int(index_tip.y * WEBCAM_HEIGHT)

                # Calculate distance for pinch detection
                pinch_dist = np.hypot(x_thumb - x_index, y_thumb - y_index)

                if hand_label == "Left":
                    left_hand_landmarks = hand_landmarks
                    if pinch_dist < PINCH_THRESHOLD:
                        is_left_pinch = True
                elif hand_label == "Right":
                    right_hand_landmarks = hand_landmarks
                    if pinch_dist < PINCH_THRESHOLD:
                        is_right_pinch = True

        # Check if both hands are detected to define the screenshot area
        if left_hand_landmarks and right_hand_landmarks:
            # Extract the 4 key points (thumbs and index fingers)
            left_thumb = left_hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            left_index = left_hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            right_thumb = right_hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            right_index = right_hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

            points = [left_thumb, left_index, right_thumb, right_index]

            screen_coords = [(p.x * SCREEN_WIDTH, p.y * SCREEN_HEIGHT) for p in points]
            frame_coords = [(int(p.x * WEBCAM_WIDTH), int(p.y * WEBCAM_HEIGHT)) for p in points]

            x_coords = [c[0] for c in screen_coords]
            y_coords = [c[1] for c in screen_coords]

            x1, y1 = min(x_coords), min(y_coords)
            x2, y2 = max(x_coords), max(y_coords)
            width, height = x2 - x1, y2 - y1

            # Draw semi-transparent overlay on the webcam feed
            frame_x1, frame_y1 = min(c[0] for c in frame_coords), min(c[1] for c in frame_coords)
            frame_x2, frame_y2 = max(c[0] for c in frame_coords), max(c[1] for c in frame_coords)
            cv2.rectangle(overlay_frame, (frame_x1, frame_y1), (frame_x2, frame_y2), (0, 255, 0, 128), -1)
            frame = cv2.addWeighted(overlay_frame, 0.3, frame, 0.7, 0)

            # --- LIVE SCREEN PREVIEW WINDOW ---
            if width > 0 and height > 0:
                try:
                    preview_pil = pyautogui.screenshot(region=(int(x1), int(y1), int(width), int(height)))
                    preview_np = np.array(preview_pil)
                    preview_bgr = cv2.cvtColor(preview_np, cv2.COLOR_RGB2BGR)

                    # Resize preview to a manageable size, maintaining aspect ratio
                    preview_h, preview_w, _ = preview_bgr.shape
                    display_width = 600
                    display_height = int(display_width * (preview_h / preview_w))
                    if display_height > 0:
                        resized_preview = cv2.resize(preview_bgr, (display_width, display_height))
                        cv2.imshow('Screen Preview', resized_preview)
                        preview_window_open = True
                except Exception:
                    # Silently ignore errors if the region is invalid for a frame
                    pass

            draw_text(frame, "Frame area. Pinch one hand to capture.", (10, 50), color=(0, 255, 255))

            # --- SCREENSHOT TRIGGER LOGIC ---
            is_pinch_trigger = (is_left_pinch and not is_right_pinch) or (is_right_pinch and not is_left_pinch)
            current_time = time.time()

            if is_pinch_trigger and (current_time - last_screenshot_time > SCREENSHOT_COOLDOWN):
                last_screenshot_time = current_time
                try:
                    # FIX: Cast region values to integers
                    region_tuple = (int(x1), int(y1), int(width), int(height))
                    screenshot = pyautogui.screenshot(region=region_tuple)

                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    filename = os.path.join(SCREENSHOTS_DIR, f"GestureShot_{timestamp}.png")
                    screenshot.save(filename)
                    print(f"Screenshot saved to {filename}")
                    draw_text(frame, "Screenshot Saved!", (int(WEBCAM_WIDTH / 2) - 150, int(WEBCAM_HEIGHT / 2)), color=(0, 255, 0), font_scale=1.5)

                except Exception as e:
                    print(f"Error taking screenshot: {e}")
                    draw_text(frame, "Error!", (int(WEBCAM_WIDTH / 2) - 50, int(WEBCAM_HEIGHT / 2)), color=(0, 0, 255), font_scale=1.5)
        else:
            # Guide the user and close the preview window if it's open
            draw_text(frame, "Show both hands to start", (10, 50), color=(0, 0, 255))
            if preview_window_open:
                cv2.destroyWindow('Screen Preview')
                preview_window_open = False

        # Display the cooldown timer on screen
        if time.time() - last_screenshot_time < SCREENSHOT_COOLDOWN:
            cooldown_remaining = int(SCREENSHOT_COOLDOWN - (time.time() - last_screenshot_time)) + 1
            draw_text(frame, f"Cooldown: {cooldown_remaining}s", (WEBCAM_WIDTH - 250, 50), color=(255, 165, 0))

        # Show the final frame
        cv2.imshow('GestureShot', frame)

        # Break the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # --- CLEANUP ---
    print("Closing application...")
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

