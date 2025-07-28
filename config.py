"""
Configuration file for Unitree G1 Autonomous Mode
"""
import os
from typing import Dict, Any

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-pro"

def validate_api_key(api_key: str = None) -> bool:
    """
    Validate Gemini API key format and availability
    
    Args:
        api_key: API key to validate (uses config default if None)
        
    Returns:
        bool: True if valid, False otherwise
    """
    key = api_key or GEMINI_API_KEY
    if not key:
        return False
    
    # Basic format validation for Google API keys
    if not key.startswith("AIza") or len(key) < 30:
        return False
        
    return True

# Robot Safety Limits
MAX_FORWARD_SPEED = 0.3  # m/s
MAX_SIDE_SPEED = 0.2     # m/s  
MAX_YAW_SPEED = 0.3      # rad/s
MIN_OBSTACLE_DISTANCE = 2.0  # meters

# Camera Configuration
CAMERA_INDEX = 0  # Front camera
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# Control Loop Configuration
LOOP_RATE = 10  # Hz (0.1 second intervals)
AI_QUERY_INTERVAL = 1.0  # seconds between AI queries

# Movement Commands
MOVEMENT_COMMANDS = {
    "move_forward": {"forward": MAX_FORWARD_SPEED, "side": 0, "yaw": 0},
    "move_backward": {"forward": -MAX_FORWARD_SPEED/2, "side": 0, "yaw": 0},
    "turn_left": {"forward": 0, "side": 0, "yaw": MAX_YAW_SPEED},
    "turn_right": {"forward": 0, "side": 0, "yaw": -MAX_YAW_SPEED},
    "strafe_left": {"forward": 0, "side": MAX_SIDE_SPEED, "yaw": 0},
    "strafe_right": {"forward": 0, "side": -MAX_SIDE_SPEED, "yaw": 0},
    "stop": {"forward": 0, "side": 0, "yaw": 0}
}

# AI Prompt Template
AI_PROMPT = """
Analyze this image from a humanoid robot's front camera. You are controlling a Unitree G1 robot.

Focus on:
1. Obstacles within 2 meters ahead
2. Clear paths for navigation
3. Ground conditions and safety
4. Any people or animals that should be avoided

Respond with ONE of these exact commands:
- "move_forward" - if path ahead is clear for at least 2 meters
- "turn_left" - if obstacle ahead, clear space to the left
- "turn_right" - if obstacle ahead, clear space to the right
- "move_backward" - if surrounded or need to retreat
- "stop" - if unsafe conditions or people nearby

Also provide a brief reason (1 sentence) for your decision.
Format: ACTION: [command] REASON: [explanation]
"""