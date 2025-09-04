# Acknowledgment:
# Inspired by the hand gesture filtering project by Harsh Kakadiya.
# Original Project: https://github.com/harsh-kakadiya1/computer-vision/tree/main/Vision-Gestures

import cv2
import numpy as np
import mediapipe as mp
import pyautogui
import os
import time

# --- CONFIGURATION ---

# The directory where screenshots will be saved.
SCREENSHOTS_DIR = "screenshots"

# Defines how close to the webcam edge a hand must be to snap to the screen edge.
EDGE_MARGIN = 0.08  # 8% of the width/height

# Controls the smoothness of the selection rectangle's movement.
# A lower value results in smoother motion but introduces more lag.
SMOOTHING_FACTOR = 0.2

# The duration of the capture countdown in seconds.
CAPTURE_COUNTDOWN_SECONDS = 3

# The cooldown period between taking screenshots.
SCREENSHOT_COOLDOWN = 3

# --- INITIALIZATION ---

# Ensure the directory for saving screenshots exists.
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)

# Initialize MediaPipe Hands for hand tracking.
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils

# Set up screen and webcam dimensions.
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

ret, frame = cap.read()
if not ret:
    print("Error: Could not read frame from webcam.")
    cap.release()
    exit()
WEBCAM_HEIGHT, WEBCAM_WIDTH, _ = frame.shape

# --- APPLICATION STATE VARIABLES ---

# Stores the smoothed corner coordinates of the selection box.
smoothed_coords = None

# Tracks whether the application is in capture mode (countdown active).
is_capture_mode = False
countdown_start_time = 0

# Stores the screen region that is locked in for capture.
locked_region = None

# Tracks the last time a screenshot was taken to manage cooldown.
last_screenshot_time = 0

# Tracks the last time hands were successfully detected to prevent flickering.
last_detection_time = 0


# --- HELPER FUNCTIONS ---

def draw_text(frame, text, position, color=(255, 255, 255), font_scale=1, thickness=2):
    """Draws text with a black outline for better visibility on any background."""
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 3)
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)


def is_pinky_up(hand_landmarks):
    """
    Checks if the pinky finger is extended upwards.
    Returns True if the pinky tip's y-coordinate is significantly above its base knuckle.
    """
    if not hand_landmarks:
        return False

    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    pinky_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]  # The knuckle at the base

    # In MediaPipe, a lower y-coordinate means higher up on the landmark map.
    return pinky_tip.y < pinky_mcp.y


# --- MAIN APPLICATION LOOP ---
try:
    preview_window_open = False
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)  # Mirror the frame for a more intuitive experience

        # Convert frame to RGB for MediaPipe processing.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        # Reset hand tracking variables for the current frame.
        left_hand_landmarks, right_hand_landmarks = None, None

        if results.multi_hand_landmarks and len(results.multi_hand_landmarks) <= 2:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                label = results.multi_handedness[hand_idx].classification[0].label

                if label == "Left":
                    left_hand_landmarks = hand_landmarks
                else:
                    right_hand_landmarks = hand_landmarks

        # --- SELECTION AND CAPTURE LOGIC ---
        # This block runs only when both hands are visible on screen.
        if left_hand_landmarks and right_hand_landmarks:
            last_detection_time = time.time()  # Update timestamp for hand detection

            # Define the four corners of the selection area using thumbs and index fingers.
            points = [
                left_hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
                right_hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
                right_hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP],
                left_hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            ]

            # --- Edge Snapping ---
            # If a hand is near the edge, snap the selection to the full screen dimension.
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
                raw_coords.append((nx * SCREEN_WIDTH, ny * SCREEN_HEIGHT))

            # --- Coordinate Smoothing ---
            # Apply an exponential moving average to dampen jitter from hand tremors.
            current_box = (min(c[0] for c in raw_coords), min(c[1] for c in raw_coords),
                           max(c[0] for c in raw_coords), max(c[1] for c in raw_coords))

            if smoothed_coords is None:
                smoothed_coords = current_box
            else:
                smoothed_coords = tuple(
                    (SMOOTHING_FACTOR * current) + ((1 - SMOOTHING_FACTOR) * smoothed)
                    for current, smoothed in zip(current_box, smoothed_coords)
                )

            sx1, sy1, sx2, sy2 = [int(c) for c in smoothed_coords]
            s_width, s_height = sx2 - sx1, sy2 - sy1

            # Clamp coordinates to be within screen bounds. This prevents screenshot errors.
            sx1 = max(0, sx1)
            sy1 = max(0, sy1)
            # Adjust width/height to not exceed screen boundaries from the new sx1, sy1
            s_width = min(SCREEN_WIDTH - sx1, s_width)
            s_height = min(SCREEN_HEIGHT - sy1, s_height)

            # --- Capture Trigger: "Raise a Pinky" ---
            is_trigger_gesture = is_pinky_up(left_hand_landmarks) or is_pinky_up(right_hand_landmarks)

            if not is_capture_mode:
                if is_trigger_gesture:
                    is_capture_mode = True
                    countdown_start_time = time.time()
                    locked_region = (sx1, sy1, s_width, s_height)
            else:  # In capture mode
                if not is_trigger_gesture:  # Lowering the pinky cancels the capture
                    is_capture_mode = False

                time_left = CAPTURE_COUNTDOWN_SECONDS - (time.time() - countdown_start_time)
                if time_left > 0:
                    draw_text(frame, str(int(time_left) + 1), (WEBCAM_WIDTH // 2 - 30, WEBCAM_HEIGHT // 2 + 30), font_scale=3, color=(255, 255, 0))
                else:  # Countdown finished, take the screenshot
                    if time.time() - last_screenshot_time > SCREENSHOT_COOLDOWN:
                        last_screenshot_time = time.time()
                        try:
                            screenshot = pyautogui.screenshot(region=locked_region)
                            filename = os.path.join(SCREENSHOTS_DIR, f"GestureShot_{time.strftime('%Y%m%d-%H%M%S')}.png")
                            screenshot.save(filename)
                            draw_text(frame, "Saved!", (WEBCAM_WIDTH // 2 - 100, WEBCAM_HEIGHT // 2), color=(0, 255, 0), font_scale=2)
                        except Exception as e:
                            print(f"Error taking screenshot: {e}")
                    is_capture_mode = False

            # --- VISUAL FEEDBACK ---
            rect_color = (0, 255, 0)  # Green: Framing
            if is_snapped and not is_capture_mode: rect_color = (255, 0, 0)  # Blue: Snapped
            if is_capture_mode: rect_color = (0, 255, 255)  # Yellow: Locked-in

            # Draw the selection area on the webcam feed
            frame_x1 = int(min(p.x for p in points) * WEBCAM_WIDTH)
            frame_y1 = int(min(p.y for p in points) * WEBCAM_HEIGHT)
            frame_x2 = int(max(p.x for p in points) * WEBCAM_WIDTH)
            frame_y2 = int(max(p.y for p in points) * WEBCAM_HEIGHT)

            overlay = frame.copy()
            cv2.rectangle(overlay, (frame_x1, frame_y1), (frame_x2, frame_y2), rect_color, -1)
            frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
            cv2.rectangle(frame, (frame_x1, frame_y1), (frame_x2, frame_y2), rect_color, 2)
            draw_text(frame, "Raise a pinky to capture", (10, 50), color=(0, 255, 255))

            # Display a live preview of the selected screen area
            if s_width > 0 and s_height > 0:
                try:
                    preview_pil = pyautogui.screenshot(region=(sx1, sy1, s_width, s_height))
                    preview_bgr = cv2.cvtColor(np.array(preview_pil), cv2.COLOR_RGB2BGR)
                    display_w = 600
                    display_h = int(display_w * s_height / s_width) if s_width > 0 else 0
                    if display_h > 0:
                        cv2.imshow('Screen Preview', cv2.resize(preview_bgr, (display_w, display_h)))
                        preview_window_open = True
                except Exception as e:
                    # Print an error to the console for debugging, but don't crash.
                    print(f"Could not create preview: {e}")
        else:
            # If hands are not detected, reset the state and close the preview window
            smoothed_coords = None
            is_capture_mode = False
            # Add a grace period before closing the window to prevent flickering
            if preview_window_open and (time.time() - last_detection_time > 0.5):
                cv2.destroyWindow('Screen Preview')
                preview_window_open = False
            draw_text(frame, "Show both hands to start", (10, 50), color=(0, 0, 255))

        cv2.imshow('GestureShot', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    # --- CLEANUP ---
    print("Closing application...")
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

