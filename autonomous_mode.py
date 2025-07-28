#!/usr/bin/env python3
"""
Fully Autonomous Mode for Unitree G1 Humanoid Robot
Integrates camera capture, AI vision analysis, and movement control
for independent navigation in unknown environments.

Author: Generated with Claude Code
Version: 1.0
"""

import time
import logging
import signal
import sys
from typing import Optional, Dict
from datetime import datetime

# Import our custom modules
from camera_module import CameraCapture
from ai_vision import GeminiVisionAnalyzer
from robot_control import RobotController
from config import LOOP_RATE, AI_QUERY_INTERVAL

class AutonomousRobot:
    """
    Main autonomous robot controller that integrates all subsystems
    """
    
    def __init__(self, simulation_mode: bool = False):
        """
        Initialize autonomous robot system
        
        Args:
            simulation_mode: Run in simulation without hardware
        """
        self.simulation_mode = simulation_mode
        self.running = False
        self.logger = self._setup_logging()
        
        # Initialize subsystems
        self.camera = CameraCapture()
        self.ai_vision = GeminiVisionAnalyzer()
        self.robot_control = RobotController(simulation_mode)
        
        # Timing control
        self.loop_interval = 1.0 / LOOP_RATE
        self.ai_query_interval = AI_QUERY_INTERVAL
        self.last_ai_query = 0.0
        
        # State tracking
        self.current_action = "stop"
        self.last_decision = None
        self.statistics = {
            'start_time': 0.0,
            'total_frames': 0,
            'ai_queries': 0,
            'movement_commands': 0,
            'safety_stops': 0
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self) -> logging.Logger:
        """
        Setup logging configuration
        
        Returns:
            logging.Logger: Configured logger
        """
        # Create logger
        logger = logging.getLogger('AutonomousRobot')
        logger.setLevel(logging.INFO)
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(f'autonomous_robot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def initialize(self) -> bool:
        """
        Initialize all subsystems
        
        Returns:
            bool: True if all systems initialized successfully
        """
        self.logger.info("Initializing autonomous robot systems...")
        
        # Initialize camera
        if not self.camera.initialize():
            self.logger.error("Failed to initialize camera system")
            return False
        
        # Initialize AI vision
        if not self.ai_vision.initialize():
            self.logger.error("Failed to initialize AI vision system")
            return False
        
        # Initialize robot control
        if not self.robot_control.initialize():
            self.logger.error("Failed to initialize robot control system")
            return False
        
        self.logger.info("All systems initialized successfully")
        return True
    
    def _signal_handler(self, signum, frame):
        """
        Handle shutdown signals gracefully
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self.logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop()
    
    def capture_and_analyze(self) -> Optional[Dict]:
        """
        Capture camera frame and analyze with AI
        
        Returns:
            dict: AI analysis result or None if failed
        """
        try:
            # Capture frame
            frame = self.camera.capture_frame()
            if frame is None:
                self.logger.warning("Failed to capture camera frame")
                return None
            
            self.statistics['total_frames'] += 1
            
            # Convert to PIL image for AI analysis
            pil_image = self.camera.frame_to_pil(frame)
            if pil_image is None:
                self.logger.warning("Failed to convert frame to PIL image")
                return None
            
            # Analyze with AI (with rate limiting)
            current_time = time.time()
            if current_time - self.last_ai_query >= self.ai_query_interval:
                analysis_result = self.ai_vision.analyze_image(pil_image)
                if analysis_result:
                    self.last_ai_query = current_time
                    self.statistics['ai_queries'] += 1
                    return analysis_result
                else:
                    self.logger.warning("AI analysis failed")
            
            # Return last decision if within query interval
            return self.last_decision
            
        except Exception as e:
            self.logger.error(f"Capture and analyze failed: {e}")
            return None
    
    def execute_decision(self, decision: Dict) -> bool:
        """
        Execute movement decision from AI analysis
        
        Args:
            decision: AI decision dictionary
            
        Returns:
            bool: True if command executed successfully
        """
        try:
            if not decision:
                return False
            
            action = decision.get('action', 'stop')
            reason = decision.get('reason', 'No reason provided')
            confidence = decision.get('confidence', 0.0)
            
            # Log decision
            self.logger.info(f"AI Decision: {action} (confidence: {confidence:.2f}) - {reason}")
            
            # Safety check before movement
            if not self.robot_control.is_safe_to_move():
                self.logger.warning("Safety conditions not met, stopping robot")
                self.robot_control.stop_move()
                self.statistics['safety_stops'] += 1
                return False
            
            # Execute movement command
            success = self.robot_control.execute_ai_command(action)
            if success:
                self.current_action = action
                self.statistics['movement_commands'] += 1
                self.logger.debug (f"Movement command '{action}' executed successfully")
            else:
                self.logger.warning(f"Failed to execute movement command '{action}'")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Decision execution failed: {e}")
            return False
    
    def autonomous_loop(self):
        """
        Main autonomous navigation loop
        """
        self.logger.info("Starting autonomous navigation loop")
        self.statistics['start_time'] = time.time()
        
        while self.running:
            loop_start_time = time.time()
            
            try:
                # Update robot state
                self.robot_control.update_state()
                
                # Check safety conditions
                if not self.robot_control.is_safe_to_move():
                    self.logger.warning("Safety conditions failed, stopping")
                    self.robot_control.stop_move()
                    self.statistics['safety_stops'] += 1
                    time.sleep(1.0)  # Wait before retrying
                    continue
                
                # Capture and analyze environment
                decision = self.capture_and_analyze()
                
                if decision:
                    # Execute AI decision
                    self.execute_decision(decision)
                    self.last_decision = decision
                else:
                    # Fallback: stop if no decision available
                    if self.current_action != "stop":
                        self.logger.info("No AI decision available, stopping as fallback")
                        self.robot_control.stop_move()
                        self.current_action = "stop"
                
                # Log periodic status
                if self.statistics['total_frames'] % 100 == 0:
                    self._log_status()
                
            except Exception as e:
                self.logger.error(f"Error in autonomous loop: {e}")
                # Emergency stop on unexpected error
                self.robot_control.stop_move()
                time.sleep(1.0)
            
            # Maintain loop timing
            loop_duration = time.time() - loop_start_time
            sleep_time = max(0, self.loop_interval - loop_duration)
            time.sleep(sleep_time)
        
        self.logger.info("Autonomous loop ended")
    
    def _log_status(self):
        """
        Log current system status
        """
        runtime = time.time() - self.statistics['start_time']
        robot_info = self.robot_control.get_robot_info()
        
        status_msg = (
            f"Status Update - Runtime: {runtime:.1f}s, "
            f"Frames: {self.statistics['total_frames']}, "
            f"AI Queries: {self.statistics['ai_queries']}, "
            f"Commands: {self.statistics['movement_commands']}, "
            f"Safety Stops: {self.statistics['safety_stops']}, "
            f"Current Action: {self.current_action}, "
            f"Battery: {robot_info['state'].battery_level:.1f}%"
        )
        
        self.logger.info(status_msg)
    
    def start(self):
        """
        Start autonomous mode
        """
        if self.running:
            self.logger.warning("Autonomous mode already running")
            return
        
        self.logger.info("Starting autonomous mode...")
        
        # Initialize systems
        if not self.initialize():
            self.logger.error("System initialization failed")
            return
        
        # Start autonomous loop
        self.running = True
        
        try:
            self.autonomous_loop()
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Autonomous mode error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """
        Stop autonomous mode gracefully
        """
        if not self.running:
            return
        
        self.logger.info("Stopping autonomous mode...")
        self.running = False
        
        # Stop robot movement
        self.robot_control.stop_move()
        
        # Shutdown subsystems
        self.robot_control.shutdown()
        self.camera.release()
        
        # Log final statistics
        self._log_final_stats()
        
        self.logger.info("Autonomous mode stopped")
    
    def _log_final_stats(self):
        """
        Log final run statistics
        """
        if self.statistics['start_time'] > 0:
            runtime = time.time() - self.statistics['start_time']
            
            # Prevent division by zero
            avg_fps = self.statistics['total_frames'] / runtime if runtime > 0 else 0.0
            ai_rate = self.statistics['ai_queries'] / runtime if runtime > 0 else 0.0
            
            stats_msg = (
                f"Final Statistics:\n"
                f"  Total Runtime: {runtime:.1f} seconds\n"
                f"  Frames Processed: {self.statistics['total_frames']}\n"
                f"  AI Queries: {self.statistics['ai_queries']}\n"
                f"  Movement Commands: {self.statistics['movement_commands']}\n"
                f"  Safety Stops: {self.statistics['safety_stops']}\n"
                f"  Average FPS: {avg_fps:.1f}\n"
                f"  AI Query Rate: {ai_rate:.2f} Hz"
            )
            
            self.logger.info(stats_msg)

def main():
    """
    Main entry point for autonomous robot
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Unitree G1 Autonomous Navigation')
    parser.add_argument('--sim', action='store_true', 
                       help='Run in simulation mode without hardware')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Set logging level')
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and start autonomous robot
    robot = AutonomousRobot(simulation_mode=args.sim)
    
    print("=== Unitree G1 Autonomous Navigation System ===")
    print(f"Mode: {'Simulation' if args.sim else 'Hardware'}")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        robot.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        robot.stop()

if __name__ == "__main__":
    main()