"""
Camera capture module for Unitree G1 robot
Handles OpenCV camera interface and image processing for AI analysis
"""

import cv2
import numpy as np
import base64
import io
from PIL import Image
from typing import Optional
import logging
from config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT, FPS

class CameraCapture:
    """
    Camera capture class for Unitree G1 robot
    Provides methods to capture frames and prepare them for AI analysis
    """
    
    def __init__(self, camera_index: int = CAMERA_INDEX):
        """
        Initialize camera capture
        
        Args:
            camera_index: Index of camera to use (0 for front camera)
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)
        
    def initialize(self) -> bool:
        """
        Initialize camera connection
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera {self.camera_index}")
                return False
                
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, FPS)
            
            # Test capture
            ret, frame = self.cap.read()
            if not ret:
                self.logger.error("Failed to capture test frame")
                return False
                
            self.is_initialized = True
            self.logger.info(f"Camera {self.camera_index} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Camera initialization failed: {e}")
            return False
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from camera
        
        Returns:
            numpy.ndarray: Captured frame or None if failed
        """
        if not self.is_initialized or self.cap is None:
            self.logger.error("Camera not initialized")
            return None
            
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning("Failed to capture frame")
                return None
                
            return frame
            
        except Exception as e:
            self.logger.error(f"Frame capture failed: {e}")
            return None
    
    def frame_to_base64(self, frame: np.ndarray, format: str = 'JPEG') -> Optional[str]:
        """
        Convert OpenCV frame to base64 string for API transmission
        
        Args:
            frame: OpenCV frame (BGR format)
            format: Image format ('JPEG' or 'PNG')
            
        Returns:
            str: Base64 encoded image or None if failed
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convert to bytes
            buffer = io.BytesIO()
            pil_image.save(buffer, format=format, quality=85)
            buffer.seek(0)
            
            # Encode to base64
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return img_base64
            
        except Exception as e:
            self.logger.error(f"Base64 conversion failed: {e}")
            return None
    
    def frame_to_pil(self, frame: np.ndarray) -> Optional[Image.Image]:
        """
        Convert OpenCV frame to PIL Image for Gemini API
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            PIL.Image: Converted image or None if failed
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            return pil_image
            
        except Exception as e:
            self.logger.error(f"PIL conversion failed: {e}")
            return None
    
    def get_frame_info(self) -> dict:
        """
        Get current camera frame information
        
        Returns:
            dict: Frame information including resolution, FPS
        """
        if not self.is_initialized or self.cap is None:
            return {}
            
        try:
            info = {
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'format': int(self.cap.get(cv2.CAP_PROP_FORMAT)),
                'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
                'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST),
                'saturation': self.cap.get(cv2.CAP_PROP_SATURATION)
            }
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get frame info: {e}")
            return {}
    
    def release(self):
        """
        Release camera resources
        """
        try:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                self.logger.info("Camera released successfully")
                
            self.is_initialized = False
            
        except Exception as e:
            self.logger.error(f"Camera release failed: {e}")
        finally:
            # Ensure OpenCV cleanup
            import cv2
            cv2.destroyAllWindows()
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        return False  # Don't suppress exceptions

# Utility functions for camera testing
def test_camera_capture():
    """
    Test camera capture functionality
    """
    logging.basicConfig(level=logging.INFO)
    
    with CameraCapture() as camera:
        if not camera.is_initialized:
            print("Failed to initialize camera")
            return
            
        print("Camera info:", camera.get_frame_info())
        
        # Capture test frame
        frame = camera.capture_frame()
        if frame is not None:
            print(f"Captured frame shape: {frame.shape}")
            
            # Test base64 conversion
            base64_str = camera.frame_to_base64(frame)
            if base64_str:
                print(f"Base64 conversion successful, length: {len(base64_str)}")
            
            # Test PIL conversion
            pil_img = camera.frame_to_pil(frame)
            if pil_img:
                print(f"PIL conversion successful, size: {pil_img.size}")
                
            # Save test image
            cv2.imwrite('test_capture.jpg', frame)
            print("Test image saved as test_capture.jpg")
        else:
            print("Failed to capture frame")

if __name__ == "__main__":
    test_camera_capture()