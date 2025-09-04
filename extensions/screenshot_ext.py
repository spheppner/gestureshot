import cv2
import pyautogui
import os
import time
from PIL import Image
from .base_extension import GestureExtension

# --- CONFIGURATION ---
SCREENSHOTS_DIR = "screenshots"
EDGE_MARGIN = 0.08
SMOOTHING_FACTOR = 0.2
CAPTURE_COUNTDOWN_SECONDS = 3
SCREENSHOT_COOLDOWN = 3
PREVIEW_WIDTH = 480
PREVIEW_UPDATE_INTERVAL = 0.2  # Update preview 5 times per second (1 / 0.2 = 5)


class ScreenshotExtension(GestureExtension):
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.mp_hands = self.app.mp_hands

        # --- State ---
        self.smoothed_coords = None
        self.is_capture_mode = False
        self.countdown_start_time = 0
        self.locked_region = None
        self.last_screenshot_time = 0
        self.saved_message_end_time = 0

        # --- Performance State ---
        self.last_preview_update_time = 0
        self.cached_preview_image = None

        if not os.path.exists(SCREENSHOTS_DIR):
            os.makedirs(SCREENSHOTS_DIR)

    def check_for_activation(self, results, frame):
        # Activate if two hands are detected
        return results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2

    def process_gestures(self, results, frame):
        # Deactivate if we lose two hands
        if not (results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2):
            self.reset_state()
            self.app.release_active_extension()
            return

        left_hand_landmarks, right_hand_landmarks = None, None
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            label = results.multi_handedness[hand_idx].classification[0].label
            if label == "Left":
                left_hand_landmarks = hand_landmarks
            else:
                right_hand_landmarks = hand_landmarks

        if not (left_hand_landmarks and right_hand_landmarks): return

        points = [
            left_hand_landmarks.landmark[self.app.mp_hands.HandLandmark.INDEX_FINGER_TIP],
            right_hand_landmarks.landmark[self.app.mp_hands.HandLandmark.INDEX_FINGER_TIP],
            right_hand_landmarks.landmark[self.app.mp_hands.HandLandmark.THUMB_TIP],
            left_hand_landmarks.landmark[self.app.mp_hands.HandLandmark.THUMB_TIP]
        ]

        _, raw_coords = self._apply_edge_snapping(points)
        self._smooth_coordinates(raw_coords)

        sx1, sy1, sx2, sy2 = [int(c) for c in self.smoothed_coords]
        s_width, s_height = self._clamp_coordinates(sx1, sy1, sx2 - sx1, sy2 - sy1)

        is_trigger_gesture = self._is_pinky_up(left_hand_landmarks) or self._is_pinky_up(right_hand_landmarks)
        self._handle_capture_mode(frame, is_trigger_gesture, (sx1, sy1, s_width, s_height))

    def draw_feedback(self, frame):
        # This is where the preview is generated, now throttled
        preview_img = self._update_preview()

        # Draw visual feedback on the webcam frame
        if self.smoothed_coords:
            points_norm = [
                (c[0] / self.app.SCREEN_WIDTH, c[1] / self.app.SCREEN_HEIGHT)
                for c in [(self.smoothed_coords[0], self.smoothed_coords[1]),
                          (self.smoothed_coords[2], self.smoothed_coords[3])]
            ]

            rect_color = (0, 255, 0)  # Green: Framing
            if self.is_capture_mode: rect_color = (0, 255, 255)  # Yellow: Locked-in

            frame_x1 = int(points_norm[0][0] * self.app.WEBCAM_WIDTH)
            frame_y1 = int(points_norm[0][1] * self.app.WEBCAM_HEIGHT)
            frame_x2 = int(points_norm[1][0] * self.app.WEBCAM_WIDTH)
            frame_y2 = int(points_norm[1][1] * self.app.WEBCAM_HEIGHT)

            overlay = frame.copy()
            cv2.rectangle(overlay, (frame_x1, frame_y1), (frame_x2, frame_y2), rect_color, -1)
            frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
            cv2.rectangle(frame, (frame_x1, frame_y1), (frame_x2, frame_y2), rect_color, 2)
            self.app.draw_text(frame, "Raise pinky to capture", (10, 30))

        if self.is_capture_mode:
            time_left = CAPTURE_COUNTDOWN_SECONDS - (time.time() - self.countdown_start_time)
            if time_left > 0:
                self.app.draw_text(frame, str(int(time_left) + 1), (self.app.WEBCAM_WIDTH // 2 - 30, self.app.WEBCAM_HEIGHT // 2 + 30), font_scale=3, color=(255, 255, 0))

        if time.time() < self.saved_message_end_time:
            self.app.draw_text(frame, "Saved!", (self.app.WEBCAM_WIDTH // 2 - 100, self.app.WEBCAM_HEIGHT // 2), color=(0, 255, 0), font_scale=2)

        return frame, preview_img

    def _update_preview(self):
        """
        Takes a screenshot for the preview, but only if enough time has passed
        since the last one. Otherwise, returns the cached image.
        """
        current_time = time.time()
        if current_time - self.last_preview_update_time < PREVIEW_UPDATE_INTERVAL:
            return self.cached_preview_image  # Return the old one

        self.last_preview_update_time = current_time

        if self.smoothed_coords:
            sx1, sy1, sx2, sy2 = [int(c) for c in self.smoothed_coords]
            width, height = sx2 - sx1, sy2 - sy1

            if width > 0 and height > 0:
                try:
                    preview_pil = pyautogui.screenshot(region=(sx1, sy1, width, height))
                    aspect_ratio = height / width if width > 0 else 1
                    display_h = int(PREVIEW_WIDTH * aspect_ratio)
                    # OPTIMIZATION: Use a faster resizing algorithm for the preview
                    self.cached_preview_image = preview_pil.resize((PREVIEW_WIDTH, display_h), Image.Resampling.BILINEAR)
                    return self.cached_preview_image
                except Exception as e:
                    # print(f"Could not create preview: {e}") # Can be noisy
                    pass

        self.cached_preview_image = None
        return None

    def _handle_capture_mode(self, frame, is_trigger_gesture, region):
        if not self.is_capture_mode:
            if is_trigger_gesture:
                self.is_capture_mode = True
                self.countdown_start_time = time.time()
                self.locked_region = region
        else:
            if not is_trigger_gesture:
                self.is_capture_mode = False
                return

            time_left = CAPTURE_COUNTDOWN_SECONDS - (time.time() - self.countdown_start_time)
            if time_left > 0:
                self.app.draw_text(frame, str(int(time_left) + 1), (self.app.WEBCAM_WIDTH // 2 - 30, self.app.WEBCAM_HEIGHT // 2 + 30), font_scale=3, color=(255, 255, 0))
            else:
                if time.time() - self.last_screenshot_time > SCREENSHOT_COOLDOWN:
                    self.last_screenshot_time = time.time()
                    try:
                        self.app.root.withdraw()
                        time.sleep(0.1)
                        screenshot = pyautogui.screenshot(region=self.locked_region)
                        self.app.root.deiconify()

                        filename = os.path.join(SCREENSHOTS_DIR, f"GestureShot_{time.strftime('%Y%m%d-%H%M%S')}.png")
                        screenshot.save(filename)
                        self.app.last_screenshot_path = filename
                        self.saved_message_end_time = time.time() + 2
                    except Exception as e:
                        print(f"Error taking screenshot: {e}")
                        if self.app.root.state() == 'withdrawn':
                            self.app.root.deiconify()
                self.is_capture_mode = False

    def reset_state(self):
        self.smoothed_coords = None
        self.is_capture_mode = False

    # --- Helper Functions ---
    def _is_pinky_up(self, hand_landmarks):
        if not hand_landmarks: return False
        pinky_tip = hand_landmarks.landmark[self.app.mp_hands.HandLandmark.PINKY_TIP]
        pinky_mcp = hand_landmarks.landmark[self.app.mp_hands.HandLandmark.PINKY_MCP]
        return pinky_tip.y < pinky_mcp.y

    def _apply_edge_snapping(self, points):
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
            raw_coords.append((nx * self.app.SCREEN_WIDTH, ny * self.app.SCREEN_HEIGHT))
        return is_snapped, raw_coords

    def _smooth_coordinates(self, raw_coords):
        current_box = (min(c[0] for c in raw_coords), min(c[1] for c in raw_coords),
                       max(c[0] for c in raw_coords), max(c[1] for c in raw_coords))
        if self.smoothed_coords is None:
            self.smoothed_coords = current_box
        else:
            self.smoothed_coords = tuple(
                (SMOOTHING_FACTOR * current) + ((1 - SMOOTHING_FACTOR) * smoothed)
                for current, smoothed in zip(current_box, self.smoothed_coords)
            )

    def _clamp_coordinates(self, x, y, w, h):
        x = max(0, x)
        y = max(0, y)
        w = min(self.app.SCREEN_WIDTH - x, w)
        h = min(self.app.SCREEN_HEIGHT - y, h)
        return w, h
