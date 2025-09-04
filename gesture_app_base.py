import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# --- CONFIGURATION ---
WEBCAM_REQ_WIDTH = 640
WEBCAM_REQ_HEIGHT = 480
PREVIEW_WIDTH = 480
UI_TRANSPARENCY = 0.75

class GestureAppBase:
    """
    The main engine for the gesture control application. It handles the camera,
    GUI, and hand tracking, but delegates all gesture logic to extensions.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Gesture Control")
        self.root.overrideredirect(True)
        self.root.configure(bg='#2e2e2e')
        self.root.resizable(False, False)
        self.root.attributes('-alpha', UI_TRANSPARENCY)
        self.root.attributes('-topmost', True)

        # --- State Variables ---
        self.last_screenshot_path = None

        # --- Extension Management ---
        self.extensions = []
        self.active_extension = None

        # --- Initialize MediaPipe & OpenCV ---
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False, max_num_hands=2,
            min_detection_confidence=0.7, min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, WEBCAM_REQ_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WEBCAM_REQ_HEIGHT)

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

        # --- Setup GUI and Position Window ---
        self.setup_gui()
        self.position_window()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.update_frame()

    def setup_gui(self):
        """Creates the Tkinter widgets for the application."""
        style = ttk.Style()
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="white", font=('Helvetica', 10))

        main_frame = ttk.Frame(self.root, padding="10 10 10 10", style="TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="Camera").grid(column=0, row=0, pady=5)
        self.webcam_label = ttk.Label(main_frame)
        self.webcam_label.grid(column=0, row=1, padx=5)

        ttk.Label(main_frame, text="Preview").grid(column=1, row=0, pady=5)
        self.preview_label = ttk.Label(main_frame)
        self.preview_label.grid(column=1, row=1, padx=5)

        aspect_ratio = self.WEBCAM_HEIGHT / self.WEBCAM_WIDTH if self.WEBCAM_WIDTH > 0 else 1
        placeholder_h = int(PREVIEW_WIDTH * aspect_ratio)
        placeholder = Image.new('RGB', (PREVIEW_WIDTH, placeholder_h), (46, 46, 46))
        self.placeholder_img = ImageTk.PhotoImage(image=placeholder)

        close_button = tk.Button(main_frame, text="✕", command=self.on_closing,
                                 bg="#2e2e2e", fg="white", font=("Arial", 10, "bold"),
                                 borderwidth=0, highlightthickness=0, relief="flat",
                                 activebackground="#c0392b", activeforeground="white")
        close_button.place(relx=1.0, x=0, y=-10, anchor="ne")

    def position_window(self):
        """
        Forces the window to render, then calculates its final size and
        moves it to the top-right corner of the screen.
        """
        self.root.withdraw()  # Hide the window temporarily
        self.root.update_idletasks()  # Force Tkinter to calculate the window's dimensions

        window_width = PREVIEW_WIDTH + self.WEBCAM_WIDTH + 70
        x_position = self.SCREEN_WIDTH - window_width

        self.root.geometry(f"+{x_position}+0")
        self.root.deiconify()  # Make the window visible again at the correct position

    def on_closing(self):
        print("Closing application...")
        if self.active_extension and hasattr(self.active_extension, 'on_close'):
            self.active_extension.on_close()
        self.cap.release()
        self.hands.close()
        self.root.destroy()

    def load_extensions(self, *extensions):
        """Initializes and stores instances of extension classes."""
        for Ext in extensions:
            self.extensions.append(Ext(self))
        print(f"Loaded {len(self.extensions)} extensions.")

    def update_frame(self):
        """The main application loop that delegates to extensions."""
        ret, frame = self.cap.read()
        if not ret:
            self.root.after(15, self.update_frame)
            return

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True

        if self.active_extension:
            self.active_extension.process_gestures(results, frame)
        else:
            for ext in self.extensions:
                if ext.check_for_activation(results, frame):
                    self.active_extension = ext
                    print(f"Activating extension: {type(ext).__name__}")
                    break

        preview_img = None
        if self.active_extension:
            frame, preview_img = self.active_extension.draw_feedback(frame)
        else:
            self.draw_text(frame, "Show hands to begin", (10, 30))

        webcam_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        webcam_photo = ImageTk.PhotoImage(image=webcam_img)
        self.webcam_label.configure(image=webcam_photo)
        self.webcam_label.image = webcam_photo

        if preview_img:
            preview_photo = ImageTk.PhotoImage(image=preview_img)
            self.preview_label.configure(image=preview_photo)
            self.preview_label.image = preview_photo
        else:
            self.preview_label.configure(image=self.placeholder_img)
            self.preview_label.image = self.placeholder_img

        self.root.after(15, self.update_frame)

    def release_active_extension(self):
        """Allows an extension to signal it's done."""
        if self.active_extension:
            print(f"Releasing extension: {type(self.active_extension).__name__}")
            self.active_extension = None

    def draw_text(self, frame, text, position, color=(255, 255, 255), font_scale=0.8, thickness=2):
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 2)
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

