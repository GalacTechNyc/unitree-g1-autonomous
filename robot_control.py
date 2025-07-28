"""
Robot movement control module for Unitree G1
Handles SDK communication and robot movement commands
"""

import time
import logging
from typing import Dict, Tuple
from dataclasses import dataclass

try:
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelWriter, ChannelReader
    from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_
    from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowState_  
    from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_
    from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowState_
    from unitree_sdk2py.utils import PosStopF, VelStopF
    UNITREE_SDK_AVAILABLE = True
except ImportError as e:
    UNITREE_SDK_AVAILABLE = False
    # Define dummy classes for simulation
    class ChannelFactoryInitialize:
        @staticmethod
        def __call__(*args, **kwargs):
            pass
    
    class ChannelWriter:
        def __init__(self, *args, **kwargs):
            pass
        def write(self, *args, **kwargs):
            pass
    
    class ChannelReader:
        def __init__(self, *args, **kwargs):
            pass  
        def read(self, *args, **kwargs):
            return None
    
    class LowCmd_:
        def __init__(self):
            self.head = [0, 0]
            self.level_flag = 0
            self.gpio = 0
            self.motor_cmd = [type('MotorCmd', (), {'mode': 0, 'q': 0, 'kp': 0, 'dq': 0, 'kd': 0, 'tau': 0})() for _ in range(20)]
    
    class LowState_:
        def __init__(self):
            self.imu_state = type('IMU', (), {'rpy': [0, 0, 0], 'gyroscope': [0, 0, 0]})()
            self.power_v = 24.0
            self.motor_state = [type('MotorState', (), {'temperature': 25.0})() for _ in range(20)]
    
    PosStopF = 0.0
    VelStopF = 0.0
    
    logging.warning(f"Unitree SDK not available ({e}), using simulation mode")

from config import (
    MAX_FORWARD_SPEED, MAX_SIDE_SPEED, MAX_YAW_SPEED, 
    MOVEMENT_COMMANDS
)

@dataclass
class RobotState:
    """Robot state information"""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # x, y, z
    orientation: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # roll, pitch, yaw
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # vx, vy, vyaw
    battery_level: float = 100.0
    temperature: float = 25.0
    is_standing: bool = False
    is_moving: bool = False
    last_update: float = 0.0

class RobotController:
    """
    Robot movement controller for Unitree G1
    Provides high-level movement commands and safety monitoring
    """
    
    def __init__(self, simulation_mode: bool = False):
        """
        Initialize robot controller
        
        Args:
            simulation_mode: If True, run in simulation without hardware
        """
        self.simulation_mode = simulation_mode or not UNITREE_SDK_AVAILABLE
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)
        
        # Robot state
        self.robot_state = RobotState()
        self.emergency_stop = False
        self.last_command_time = 0.0
        
        # SDK objects
        self.cmd_writer = None
        self.state_reader = None
        self.low_cmd = None
        self.low_state = None
        
        # Safety limits
        self.max_speeds = {
            'forward': MAX_FORWARD_SPEED,
            'side': MAX_SIDE_SPEED, 
            'yaw': MAX_YAW_SPEED
        }
        
    def initialize(self) -> bool:
        """
        Initialize robot connection and SDK
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.simulation_mode:
                self.logger.info("Running in simulation mode")
                self.is_initialized = True
                return True
            
            # Initialize SDK
            ChannelFactoryInitialize(0, "")
            
            # Create command and state objects
            self.low_cmd = LowCmd_()
            self.low_state = LowState_()
            
            # Initialize DDS communication
            self.cmd_writer = ChannelWriter("rt/lowcmd", LowCmd_)
            self.state_reader = ChannelReader("rt/lowstate", LowState_)
            
            # Initialize command
            self.low_cmd.head[0] = 0xFE
            self.low_cmd.head[1] = 0xEF
            self.low_cmd.level_flag = 0xFF
            self.low_cmd.gpio = 0
            
            # Set initial safe state
            for i in range(20):  # 20 motors
                self.low_cmd.motor_cmd[i].mode = 0x01  # Position mode
                self.low_cmd.motor_cmd[i].q = PosStopF
                self.low_cmd.motor_cmd[i].kp = 0
                self.low_cmd.motor_cmd[i].dq = VelStopF  
                self.low_cmd.motor_cmd[i].kd = 0
                self.low_cmd.motor_cmd[i].tau = 0
            
            self.is_initialized = True
            self.logger.info("Robot controller initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Robot initialization failed: {e}")
            return False
    
    def update_state(self) -> bool:
        """
        Update robot state from sensors
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.simulation_mode:
                # Update simulation state
                self.robot_state.last_update = time.time()
                return True
            
            # Read actual robot state
            if self.state_reader:
                self.low_state = self.state_reader.read()
                
                if self.low_state:
                    # Update position and orientation from IMU
                    imu = self.low_state.imu_state
                    self.robot_state.orientation = (
                        imu.rpy[0],  # roll
                        imu.rpy[1],  # pitch  
                        imu.rpy[2]   # yaw
                    )
                    
                    # Update velocity
                    self.robot_state.velocity = (
                        imu.gyroscope[0],
                        imu.gyroscope[1], 
                        imu.gyroscope[2]
                    )
                    
                    # Update battery and temperature
                    self.robot_state.battery_level = self.low_state.power_v * 10  # Rough estimate
                    self.robot_state.temperature = self.low_state.motor_state[0].temperature
                    
                    self.robot_state.last_update = time.time()
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"State update failed: {e}")
            return False
    
    def velocity_move(self, forward_speed: float, side_speed: float, yaw_speed: float) -> bool:
        """
        Move robot with specified velocities
        
        Args:
            forward_speed: Forward velocity (m/s)
            side_speed: Side velocity (m/s) 
            yaw_speed: Yaw angular velocity (rad/s)
            
        Returns:
            bool: True if command sent successfully
        """
        if self.emergency_stop:
            self.logger.warning("Emergency stop active, ignoring move command")
            return False
        
        # Apply safety limits
        forward_speed = max(-self.max_speeds['forward'], 
                           min(self.max_speeds['forward'], forward_speed))
        side_speed = max(-self.max_speeds['side'],
                        min(self.max_speeds['side'], side_speed))
        yaw_speed = max(-self.max_speeds['yaw'],
                       min(self.max_speeds['yaw'], yaw_speed))
        
        try:
            if self.simulation_mode:
                self.logger.info(f"SIM: VelocityMove({forward_speed:.2f}, {side_speed:.2f}, {yaw_speed:.2f})")
                self.robot_state.is_moving = abs(forward_speed) > 0.01 or abs(side_speed) > 0.01 or abs(yaw_speed) > 0.01
                return True
            
            # Send actual command to robot
            if self.cmd_writer and self.low_cmd:
                # Set velocity commands (this is a simplified version)
                # In actual implementation, you would need to convert 
                # high-level velocities to joint commands
                
                # For now, we'll use a placeholder implementation
                # that would need to be replaced with actual SDK calls
                self.logger.info(f"CMD: VelocityMove({forward_speed:.2f}, {side_speed:.2f}, {yaw_speed:.2f})")
                
                # Update command timestamp
                self.last_command_time = time.time()
                self.robot_state.is_moving = True
                
                # Write command
                self.cmd_writer.write(self.low_cmd)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Velocity move failed: {e}")
            return False
    
    def stop_move(self) -> bool:
        """
        Stop all robot movement
        
        Returns:
            bool: True if successful
        """
        return self.velocity_move(0.0, 0.0, 0.0)
    
    def execute_ai_command(self, action: str) -> bool:
        """
        Execute movement command from AI decision
        
        Args:
            action: Action string from AI analysis
            
        Returns:
            bool: True if command executed successfully
        """
        if action not in MOVEMENT_COMMANDS:
            self.logger.warning(f"Unknown action: {action}")
            return self.stop_move()
        
        cmd = MOVEMENT_COMMANDS[action]
        return self.velocity_move(cmd['forward'], cmd['side'], cmd['yaw'])
    
    def set_emergency_stop(self, stop: bool = True):
        """
        Set emergency stop state
        
        Args:
            stop: True to activate emergency stop, False to deactivate
        """
        self.emergency_stop = stop
        if stop:
            self.stop_move()
            self.logger.warning("EMERGENCY STOP ACTIVATED")
        else:
            self.logger.info("Emergency stop deactivated")
    
    def check_safety_conditions(self) -> Dict[str, bool]:
        """
        Check various safety conditions
        
        Returns:
            dict: Safety condition status
        """
        conditions = {
            'battery_ok': self.robot_state.battery_level > 20.0,
            'temperature_ok': self.robot_state.temperature < 80.0,
            'orientation_ok': abs(self.robot_state.orientation[0]) < 0.5 and 
                            abs(self.robot_state.orientation[1]) < 0.5,
            'recent_update': (time.time() - self.robot_state.last_update) < 1.0,
            'not_emergency': not self.emergency_stop
        }
        
        # Log any failing conditions
        for condition, status in conditions.items():
            if not status:
                self.logger.warning(f"Safety condition failed: {condition}")
        
        return conditions
    
    def is_safe_to_move(self) -> bool:
        """
        Check if it's safe to move the robot
        
        Returns:
            bool: True if safe to move
        """
        conditions = self.check_safety_conditions()
        return all(conditions.values())
    
    def get_robot_info(self) -> Dict:
        """
        Get current robot information
        
        Returns:
            dict: Robot state and status information
        """
        return {
            'state': self.robot_state,
            'is_initialized': self.is_initialized,
            'simulation_mode': self.simulation_mode,
            'emergency_stop': self.emergency_stop,
            'safety_conditions': self.check_safety_conditions(),
            'last_command_time': self.last_command_time
        }
    
    def shutdown(self):
        """
        Safely shutdown robot controller
        """
        try:
            # Stop all movement
            self.stop_move()
            
            # Wait for stop command to be processed
            time.sleep(0.1)
            
            self.logger.info("Robot controller shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")

# Utility functions for testing
def test_robot_control():
    """
    Test robot control functionality
    """
    logging.basicConfig(level=logging.INFO)
    
    controller = RobotController(simulation_mode=True)
    
    if not controller.initialize():
        print("Failed to initialize robot controller")
        return
    
    print("Robot controller initialized")
    
    # Test basic movements
    commands = ['move_forward', 'turn_left', 'turn_right', 'stop']
    
    for cmd in commands:
        print(f"Testing command: {cmd}")
        controller.execute_ai_command(cmd)
        controller.update_state()
        time.sleep(1)
    
    # Test safety conditions
    safety = controller.check_safety_conditions()
    print(f"Safety conditions: {safety}")
    
    # Test emergency stop
    controller.set_emergency_stop(True)
    print("Emergency stop test - should refuse to move")
    controller.execute_ai_command('move_forward')
    
    controller.set_emergency_stop(False)
    print("Emergency stop deactivated")
    
    controller.shutdown()
    print("Test complete")

if __name__ == "__main__":
    test_robot_control()