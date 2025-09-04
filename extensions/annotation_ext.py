from collections import deque
import time
import cv2
from .base_extension import GestureExtension
from ui.annotation_window import AnnotationWindow


class AnnotationExtension(GestureExtension):
    """
    Handles summoning and drawing on the last screenshot.
    Gestures must be held for a short duration to be recognized,
    preventing accidental triggers.
    """
    FRAMES_TO_CONFIRM_GESTURE = 15  # Approx. 0.5 seconds

    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.annotation_window = None
        self.finger_state_history = deque(maxlen=15)
        self.gesture_cooldown_end = 0

        self.current_gesture = None
        self.gesture_frame_counter = 0

    def check_for_activation(self, results, frame):
        if (results.multi_hand_landmarks and
                len(results.multi_hand_landmarks) == 1 and
                self.app.last_screenshot_path and
                time.time() > self.gesture_cooldown_end):

            if self._is_come_here_gesture(results.multi_hand_landmarks[0]):
                self.annotation_window = AnnotationWindow(self.app.root, self.app.last_screenshot_path)
                return True
        return False

    def process_gestures(self, results, frame):
        if not self.annotation_window or not self.annotation_window.root.winfo_exists():
            self.on_close()
            return

        if not results.multi_hand_landmarks:
            self.current_gesture = None
            self.gesture_frame_counter = 0
            return

        hand_landmarks = results.multi_hand_landmarks[0]

        detected_gesture = "none"
        # Check for fist first, as it's the most common action
        if self._is_fist(hand_landmarks):
            detected_gesture = "draw"
        elif self._is_thumbs_up(hand_landmarks):
            detected_gesture = "save"
        elif self._is_open_palm(hand_landmarks):
            detected_gesture = "close"

        if detected_gesture == self.current_gesture:
            self.gesture_frame_counter += 1
        else:
            self.current_gesture = detected_gesture
            self.gesture_frame_counter = 1

        if self.gesture_frame_counter > self.FRAMES_TO_CONFIRM_GESTURE:
            if self.current_gesture == "save":
                self.annotation_window.save_and_copy()
                # on_close is called implicitly after save
                return
            elif self.current_gesture == "close":
                self.annotation_window.close()
                self.on_close()
                return

        is_drawing = (self.current_gesture == "draw")
        cursor_pos = self._get_cursor_position(hand_landmarks)
        self.annotation_window.update_cursor(cursor_pos, is_drawing)

    def draw_feedback(self, frame):
        self.app.draw_text(frame, "Annotation Mode", (10, 30), color=(255, 0, 255))
        self.app.draw_text(frame, "Fist to Draw", (10, 60))
        self.app.draw_text(frame, "HOLD Thumbs-Up to Save", (10, 90))
        self.app.draw_text(frame, "HOLD Open Palm to Close", (10, 120))

        if self.current_gesture in ["save", "close"]:
            progress = min(1.0, self.gesture_frame_counter / self.FRAMES_TO_CONFIRM_GESTURE)
            bar_width = int(progress * (self.app.WEBCAM_WIDTH - 20))
            cv2.rectangle(frame, (10, self.app.WEBCAM_HEIGHT - 20), (10 + bar_width, self.app.WEBCAM_HEIGHT - 10), (0, 255, 0), -1)

        return frame, None

    def on_close(self):
        if self.annotation_window and self.annotation_window.root.winfo_exists():
            self.annotation_window.close()
        self.annotation_window = None
        self.finger_state_history.clear()
        self.gesture_cooldown_end = time.time() + 2
        self.current_gesture = None
        self.gesture_frame_counter = 0
        self.app.release_active_extension()

    # --- Gesture Detection Helpers ---
    def _is_come_here_gesture(self, hand_landmarks):
        index_tip_y = hand_landmarks.landmark[8].y
        index_pip_y = hand_landmarks.landmark[6].y
        is_curled = index_tip_y > index_pip_y

        last_state_curled = self.finger_state_history[-1] if self.finger_state_history else False
        self.finger_state_history.append(is_curled)

        if not last_state_curled and is_curled:
            if len(self.finger_state_history) > 5 and not any(list(self.finger_state_history)[-6:-1]):
                self.gesture_cooldown_end = time.time() + 3
                return True
        return False

    def _is_fist(self, hand_landmarks):
        """A robust check for a fist gesture."""
        try:
            # All four non-thumb fingers must be curled.
            # A finger is curled if its tip is vertically lower than its base knuckle.
            index_curled = hand_landmarks.landmark[8].y > hand_landmarks.landmark[5].y
            middle_curled = hand_landmarks.landmark[12].y > hand_landmarks.landmark[9].y
            ring_curled = hand_landmarks.landmark[16].y > hand_landmarks.landmark[13].y
            pinky_curled = hand_landmarks.landmark[20].y > hand_landmarks.landmark[17].y

            return all([index_curled, middle_curled, ring_curled, pinky_curled])
        except:
            return False

    def _get_cursor_position(self, hand_landmarks):
        index_tip = hand_landmarks.landmark[8]
        return (index_tip.x, index_tip.y)

    def _is_open_palm(self, hand_landmarks):
        try:
            # Fingers are extended if their tips are vertically higher than their middle joints.
            index_extended = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
            middle_extended = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
            ring_extended = hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y
            pinky_extended = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y

            return all([index_extended, middle_extended, ring_extended, pinky_extended])
        except:
            return False

    def _is_thumbs_up(self, hand_landmarks):
        try:
            # Thumb tip is vertically higher than its next joint.
            thumb_up = hand_landmarks.landmark[4].y < hand_landmarks.landmark[3].y
            # Other fingers are curled (tip below base).
            index_curled = hand_landmarks.landmark[8].y > hand_landmarks.landmark[5].y
            middle_curled = hand_landmarks.landmark[12].y > hand_landmarks.landmark[9].y

            return thumb_up and index_curled and middle_curled
        except:
            return False

