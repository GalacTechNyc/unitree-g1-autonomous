"""
Google Gemini API integration for AI-powered vision analysis
Handles image analysis and navigation decision making
"""

import google.generativeai as genai
from PIL import Image
import logging
import time
import re
from typing import Optional, Dict, Tuple
from config import GEMINI_API_KEY, GEMINI_MODEL, AI_PROMPT, validate_api_key

class GeminiVisionAnalyzer:
    """
    Google Gemini API wrapper for robot vision analysis
    Provides methods to analyze camera images and get navigation decisions
    """
    
    def __init__(self, api_key: str = GEMINI_API_KEY, model_name: str = GEMINI_MODEL):
        """
        Initialize Gemini API client
        
        Args:
            api_key: Google Gemini API key
            model_name: Model to use for analysis
        """
        self.api_key = api_key
        self.model_name = model_name
        self.model = None
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
        
    def initialize(self) -> bool:
        """
        Initialize Gemini API connection
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not validate_api_key(self.api_key):
                self.logger.error("Invalid or missing Gemini API key. Please set GEMINI_API_KEY environment variable.")
                return False
                
            # Configure API
            genai.configure(api_key=self.api_key)
            
            # Initialize model
            self.model = genai.GenerativeModel(self.model_name)
            
            # Test connection with a simple prompt
            test_response = self.model.generate_content("Test connection")
            if test_response:
                self.is_initialized = True
                self.logger.info(f"Gemini API initialized successfully with model {self.model_name}")
                return True
            else:
                self.logger.error("Failed to get test response from Gemini API")
                return False
                
        except Exception as e:
            self.logger.error(f"Gemini API initialization failed: {e}")
            return False
    
    def analyze_image(self, image: Image.Image, custom_prompt: Optional[str] = None) -> Optional[Dict]:
        """
        Analyze image using Gemini API
        
        Args:
            image: PIL Image to analyze
            custom_prompt: Custom prompt (uses default if None)
            
        Returns:
            dict: Analysis result with action and reason
        """
        if not self.is_initialized or self.model is None:
            self.logger.error("Gemini API not initialized")
            return None
            
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        try:
            prompt = custom_prompt if custom_prompt else AI_PROMPT
            
            # Generate content with image and prompt with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Gemini API request timed out")
            
            # Set timeout of 30 seconds
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            try:
                response = self.model.generate_content([image, prompt])
                self.last_request_time = time.time()
                
                if response and response.text:
                    return self._parse_response(response.text)
                else:
                    self.logger.warning("Empty response from Gemini API")
                    return None
                    
            finally:
                signal.alarm(0)  # Cancel the alarm
                
        except TimeoutError:
            self.logger.error("Gemini API request timed out after 30 seconds")
            return None
        except Exception as e:
            self.logger.error(f"Image analysis failed: {e}")
            return None
    
    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse Gemini API response to extract action and reason
        
        Args:
            response_text: Raw response from API
            
        Returns:
            dict: Parsed response with action and reason
        """
        try:
            # Look for ACTION: and REASON: patterns
            action_match = re.search(r'ACTION:\s*(\w+)', response_text, re.IGNORECASE)
            reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', response_text, re.IGNORECASE)
            
            action = None
            reason = "No reason provided"
            
            if action_match:
                action = action_match.group(1).lower()
            else:
                # Fallback: look for common action words
                response_lower = response_text.lower()
                if 'move_forward' in response_lower or 'forward' in response_lower:
                    action = 'move_forward'
                elif 'turn_left' in response_lower or 'left' in response_lower:
                    action = 'turn_left'
                elif 'turn_right' in response_lower or 'right' in response_lower:
                    action = 'turn_right'
                elif 'move_backward' in response_lower or 'backward' in response_lower:
                    action = 'move_backward'
                elif 'stop' in response_lower:
                    action = 'stop'
                else:
                    action = 'stop'  # Default safe action
            
            if reason_match:
                reason = reason_match.group(1).strip()
            else:
                reason = response_text[:100] + "..." if len(response_text) > 100 else response_text
            
            result = {
                'action': action,
                'reason': reason,
                'raw_response': response_text,
                'confidence': self._estimate_confidence(response_text),
                'timestamp': time.time()
            }
            
            self.logger.info(f"AI Decision: {action} - {reason}")
            return result
            
        except Exception as e:
            self.logger.error(f"Response parsing failed: {e}")
            return {
                'action': 'stop',
                'reason': 'Failed to parse AI response',
                'raw_response': response_text,
                'confidence': 0.0,
                'timestamp': time.time()
            }
    
    def _estimate_confidence(self, response_text: str) -> float:
        """
        Estimate confidence level based on response characteristics
        
        Args:
            response_text: Response text to analyze
            
        Returns:
            float: Confidence score (0.0 to 1.0)
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence for structured responses
        if 'ACTION:' in response_text and 'REASON:' in response_text:
            confidence += 0.3
        
        # Increase confidence for detailed reasoning
        if len(response_text) > 50:
            confidence += 0.1
        
        # Decrease confidence for uncertain language
        uncertain_terms = ['maybe', 'might', 'possibly', 'unclear', 'uncertain']
        for term in uncertain_terms:
            if term in response_text.lower():
                confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def get_safety_analysis(self, image: Image.Image) -> Optional[Dict]:
        """
        Perform safety-focused analysis of the image
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            dict: Safety analysis result
        """
        safety_prompt = """
        Analyze this image for safety concerns for a humanoid robot:
        
        1. Are there any people or animals in the scene?
        2. Are there any dangerous obstacles (stairs, holes, fragile objects)?
        3. Is the ground stable and safe for walking?
        4. Are there any moving objects or vehicles?
        
        Respond with:
        SAFETY: SAFE/CAUTION/DANGER
        CONCERNS: [list any safety concerns]
        RECOMMENDATION: [safety recommendation]
        """
        
        return self.analyze_image(image, safety_prompt)
    
    def test_connection(self) -> bool:
        """
        Test API connection with a simple request
        
        Returns:
            bool: True if connection successful
        """
        try:
            if not self.is_initialized:
                return False
                
            response = self.model.generate_content("Respond with 'OK' if you can see this.")
            return response and 'OK' in response.text.upper()
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

# Utility functions for testing
def test_gemini_api():
    """
    Test Gemini API functionality
    """
    logging.basicConfig(level=logging.INFO)
    
    analyzer = GeminiVisionAnalyzer()
    
    if not analyzer.initialize():
        print("Failed to initialize Gemini API")
        return
    
    print("API initialized successfully")
    
    # Test connection
    if analyzer.test_connection():
        print("Connection test passed")
    else:
        print("Connection test failed")
    
    # Test with a simple image (create a test image)
    try:
        from PIL import Image
        import numpy as np
        
        # Create a test image
        test_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        test_image = Image.fromarray(test_array)
        
        # Analyze test image
        result = analyzer.analyze_image(test_image)
        if result:
            print(f"Analysis successful: {result}")
        else:
            print("Analysis failed")
            
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_gemini_api()