#!/usr/bin/env python3
"""
Dependency installer for Unitree G1 Autonomous Mode
Handles installation of all required packages and SDK components
"""

import subprocess
import sys
import os
import logging

def run_command(command, description=""):
    """
    Run a shell command and handle errors
    
    Args:
        command: Command to execute
        description: Description for logging
    """
    try:
        print(f"Installing: {description}")
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✓ Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {description}")
        print(f"Error: {e.stderr}")
        return False

def install_dependencies():
    """
    Install all required dependencies
    """
    os.environ["CYCLONEDDS_HOME"] = "/Users/stephonbridges/G1SA/cyclonedds/install"
    os.environ["CPATH"] = "/Users/stephonbridges/G1SA/cyclonedds/src/core/include"
    print("=== Unitree G1 Autonomous Mode - Dependency Installation ===")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        return False
    
    print(f"Python version: {sys.version}")
    
    # Install core dependencies
    dependencies = [
        ("source venv/bin/activate && python3 -m pip install --upgrade pip", "Upgrading pip"),
        ("source venv/bin/activate && python3 -m pip install unitree_sdk2py", "Unitree SDK"),
        ("source venv/bin/activate && python3 -m pip install google-generativeai", "Google Gemini API"),
        ("source venv/bin/activate && python3 -m pip install opencv-python", "OpenCV"),
        ("source venv/bin/activate && python3 -m pip install numpy", "NumPy"),
        ("source venv/bin/activate && python3 -m pip install Pillow", "PIL/Pillow"),
        ("source venv/bin/activate && python3 -m pip install cyclonedds==0.10.2", "Cyclone DDS"),
    ]
    
    success_count = 0
    for command, description in dependencies:
        if run_command(command, description):
            success_count += 1
    
    print(f"\n=== Installation Summary ===")
    print(f"Successful: {success_count}/{len(dependencies)}")
    
    if success_count == len(dependencies):
        print("✓ All dependencies installed successfully!")
        print("\nNext steps:")
        print("1. Set your GEMINI_API_KEY environment variable")
        print("2. Run: python autonomous_mode.py --sim (for simulation)")
        print("3. Run: python autonomous_mode.py (for hardware)")
        return True
    else:
        print("✗ Some dependencies failed to install")
        print("Please check the errors above and install manually")
        return False

if __name__ == "__main__":
    install_dependencies()
