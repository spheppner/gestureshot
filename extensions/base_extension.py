from abc import ABC, abstractmethod

class GestureExtension(ABC):
    """
    An abstract base class that defines the interface for all extensions.
    """
    def __init__(self, parent_app):
        """
        Initializes the extension.
        :param parent_app: A reference to the main GestureAppBase instance.
        """
        self.app = parent_app

    @abstractmethod
    def check_for_activation(self, results, frame):
        """
        Called on every frame when no extension is active. Checks if the
        conditions to activate this extension are met (e.g., specific number
        of hands or a specific gesture).
        :return: True to activate, False otherwise.
        """
        pass

    @abstractmethod
    def process_gestures(self, results, frame):
        """
        Called on every frame ONLY when this extension is active. This is
        where the main logic of the extension runs.
        """
        pass

    @abstractmethod
    def draw_feedback(self, frame):
        """
        Called on every frame ONLY when this extension is active. Used to
        draw visual feedback (like selection boxes or text) onto the webcam frame.
        It can also return a PIL image to be displayed in the preview panel.
        :return: A tuple of (modified_frame, optional_preview_image).
        """
        pass
