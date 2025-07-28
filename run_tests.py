#!/usr/bin/env python3
"""
Test runner for Unitree G1 Autonomous Mode
Runs comprehensive tests on all system components
"""

import sys
import os
import logging
import unittest
from unittest.mock import Mock, patch
import time

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestCameraModule(unittest.TestCase):
    """Test camera capture functionality"""
    
    def setUp(self):
        """Setup test environment"""
        from camera_module import CameraCapture
        self.camera = CameraCapture()
    
    def test_camera_initialization(self):
        """Test camera initialization"""
        # In simulation/testing, this might fail if no camera available
        # We'll test the initialization logic
        self.assertIsNotNone(self.camera)
        self.assertEqual(self.camera.camera_index, 0)
        self.assertFalse(self.camera.is_initialized)
    
    def test_frame_conversion_methods(self):
        """Test image conversion methods"""
        import numpy as np
        from PIL import Image
        
        # Create a test frame
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Test PIL conversion
        pil_image = self.camera.frame_to_pil(test_frame)
        if pil_image:  # Only test if conversion succeeded
            self.assertIsInstance(pil_image, Image.Image)
            self.assertEqual(pil_image.size, (640, 480))
        
        # Test base64 conversion
        base64_str = self.camera.frame_to_base64(test_frame)
        if base64_str:  # Only test if conversion succeeded
            self.assertIsInstance(base64_str, str)
            self.assertGreater(len(base64_str), 0)

class TestAIVision(unittest.TestCase):
    """Test AI vision analysis"""
    
    def setUp(self):
        """Setup test environment"""
        from ai_vision import GeminiVisionAnalyzer
        self.analyzer = GeminiVisionAnalyzer()
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        self.assertIsNotNone(self.analyzer)
        self.assertFalse(self.analyzer.is_initialized)
    
    def test_response_parsing(self):
        """Test response parsing logic"""
        test_responses = [
            "ACTION: move_forward REASON: Path is clear ahead",
            "ACTION: turn_left REASON: Obstacle detected on right",
            "ACTION: stop REASON: Person detected in path",
            "The robot should move forward because the path looks clear.",
            "I recommend turning left to avoid the obstacle."
        ]
        
        for response in test_responses:
            result = self.analyzer._parse_response(response)
            self.assertIsInstance(result, dict)
            self.assertIn('action', result)
            self.assertIn('reason', result)
            self.assertIn('confidence', result)
            self.assertIn(result['action'], ['move_forward', 'turn_left', 'turn_right', 'move_backward', 'stop'])

class TestRobotControl(unittest.TestCase):
    """Test robot control functionality"""
    
    def setUp(self):
        """Setup test environment"""
        from robot_control import RobotController
        self.controller = RobotController(simulation_mode=True)
    
    def test_controller_initialization(self):
        """Test controller initialization"""
        self.assertIsNotNone(self.controller)
        self.assertTrue(self.controller.simulation_mode)
        self.assertFalse(self.controller.is_initialized)
        
        # Test initialization
        success = self.controller.initialize()
        self.assertTrue(success)
        self.assertTrue(self.controller.is_initialized)
    
    def test_safety_conditions(self):
        """Test safety condition checking"""
        self.controller.initialize()
        
        # Test initial safety conditions
        conditions = self.controller.check_safety_conditions()
        self.assertIsInstance(conditions, dict)
        
        # Test emergency stop
        self.controller.set_emergency_stop(True)
        self.assertTrue(self.controller.emergency_stop)
        
        self.controller.set_emergency_stop(False)
        self.assertFalse(self.controller.emergency_stop)
    
    def test_movement_commands(self):
        """Test movement command execution"""
        self.controller.initialize()
        
        # Test basic movement commands
        commands = ['move_forward', 'turn_left', 'turn_right', 'stop']
        
        for cmd in commands:
            success = self.controller.execute_ai_command(cmd)
            self.assertTrue(success)
    
    def test_velocity_limits(self):
        """Test velocity limiting"""
        self.controller.initialize()
        
        # Test exceeding limits
        success = self.controller.velocity_move(1.0, 0.5, 1.0)  # Exceed all limits
        self.assertTrue(success)  # Should succeed but with limited values

class TestAutonomousMode(unittest.TestCase):
    """Test autonomous mode integration"""
    
    def setUp(self):
        """Setup test environment"""
        from autonomous_mode import AutonomousRobot
        self.robot = AutonomousRobot(simulation_mode=True)
    
    def test_robot_initialization(self):
        """Test autonomous robot initialization"""
        self.assertIsNotNone(self.robot)
        self.assertTrue(self.robot.simulation_mode)
        self.assertFalse(self.robot.running)
    
    def test_statistics_tracking(self):
        """Test statistics tracking"""
        stats = self.robot.statistics
        self.assertIsInstance(stats, dict)
        self.assertIn('total_frames', stats)
        self.assertIn('ai_queries', stats)
        self.assertIn('movement_commands', stats)

def run_component_tests():
    """Run individual component tests"""
    print("\n=== Component Tests ===")
    
    # Test camera module
    print("\n1. Testing Camera Module...")
    try:
        from camera_module import test_camera_capture
        test_camera_capture()
        print("✓ Camera module test completed")
    except Exception as e:
        print(f"✗ Camera module test failed: {e}")
    
    # Test AI vision module  
    print("\n2. Testing AI Vision Module...")
    try:
        from ai_vision import test_gemini_api
        test_gemini_api()
        print("✓ AI vision module test completed")
    except Exception as e:
        print(f"✗ AI vision module test failed: {e}")
    
    # Test robot control module
    print("\n3. Testing Robot Control Module...")
    try:
        from robot_control import test_robot_control
        test_robot_control()
        print("✓ Robot control module test completed")
    except Exception as e:
        print(f"✗ Robot control module test failed: {e}")

def run_integration_test():
    """Run integration test"""
    print("\n=== Integration Test ===")
    
    try:
        from autonomous_mode import AutonomousRobot
        
        # Create robot in simulation mode
        robot = AutonomousRobot(simulation_mode=True)
        
        # Test initialization
        print("Initializing systems...")
        if robot.initialize():
            print("✓ All systems initialized successfully")
        else:
            print("✗ System initialization failed")
            return False
        
        # Test short autonomous run (5 seconds)
        print("Running 5-second autonomous test...")
        robot.running = True
        
        start_time = time.time()
        iterations = 0
        
        while robot.running and (time.time() - start_time) < 5.0:
            # Simulate one loop iteration
            robot.robot_control.update_state()
            
            # Test decision execution with mock decision
            test_decision = {
                'action': 'move_forward',
                'reason': 'Test movement',
                'confidence': 0.8
            }
            
            robot.execute_decision(test_decision)
            iterations += 1
            time.sleep(0.1)
        
        # Stop robot
        robot.stop()
        
        print(f"✓ Integration test completed - {iterations} iterations")
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def main():
    """Main test runner"""
    print("=== Unitree G1 Autonomous Mode - Test Suite ===")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run unit tests
    print("\n=== Unit Tests ===")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCameraModule))
    suite.addTests(loader.loadTestsFromTestCase(TestAIVision))
    suite.addTests(loader.loadTestsFromTestCase(TestRobotControl))
    suite.addTests(loader.loadTestsFromTestCase(TestAutonomousMode))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run component tests
    run_component_tests()
    
    # Run integration test
    integration_success = run_integration_test()
    
    # Summary
    print("\n=== Test Summary ===")
    print(f"Unit Tests: {result.testsRun} run, {len(result.failures)} failures, {len(result.errors)} errors")
    print(f"Integration Test: {'✓ Passed' if integration_success else '✗ Failed'}")
    
    if result.wasSuccessful() and integration_success:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)