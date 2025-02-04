import numpy as np
from typing import Dict, List, Optional
import time

from core import (
    RobotState, physical_params, gait_params,
    GaitType, LEG_LABELS
)
from kinematics import forward_kinematics, inverse_kinematics
from dynamics import (
    compute_ground_reaction_forces,
    compute_joint_torques,
    compute_com_position
)
from gaits import GaitGenerator


class QuadrupedRobot:
    def __init__(self, gait_type: GaitType = GaitType.TROT):
        # Initialize robot state
        self.state = RobotState(
            position=np.zeros(3),
            orientation=np.zeros(3),
            velocity=np.zeros(3),
            angular_velocity=np.zeros(3),
            foot_positions={leg: np.zeros(3) for leg in LEG_LABELS},
            joint_angles={leg: (0.0, 0.0) for leg in LEG_LABELS}
        )
        
        # Initialize gait generator
        self.gait_generator = GaitGenerator(gait_type)
        self.phase = 0.0
        self.time_last_update = time.time()
    
    def update(self) -> None:
        """Update robot state for next timestep"""
        current_time = time.time()
        dt = current_time - self.time_last_update
        self.time_last_update = current_time
        
        # Update phase
        self.phase = (self.phase + dt * gait_params.STEP_FREQUENCY) % 1.0
        
        # Get new foot positions from gait generator
        foot_positions = self.gait_generator.get_next_foot_positions(self.phase)
        stance_legs = self.gait_generator.get_stance_legs(self.phase)
        
        # Compute ground reaction forces for stance legs
        grf = compute_ground_reaction_forces(self.state, stance_legs)
        
        # Compute required joint torques
        torques = compute_joint_torques(self.state, grf)
        
        # Update foot positions and joint angles
        for leg_id in LEG_LABELS:
            self.state.foot_positions[leg_id] = foot_positions[leg_id]
            theta_hip, theta_knee = inverse_kinematics(
                foot_positions[leg_id][0],
                foot_positions[leg_id][1],
                foot_positions[leg_id][2]
            )
            if theta_hip is not None and theta_knee is not None:
                self.state.joint_angles[leg_id] = (theta_hip, theta_knee)
        
        # Update COM position
        com = compute_com_position(self.state)
        self.state.position = com
    
    def move_forward(self, distance: float) -> None:
        """Move robot forward by specified distance"""
        self.state.position[0] += distance
    
    def move_backward(self, distance: float) -> None:
        """Move robot backward by specified distance"""
        self.move_forward(-distance)
    
    def turn(self, angle: float) -> None:
        """Turn robot by specified angle (in radians)"""
        self.state.orientation[2] += angle
    
    def get_state(self) -> RobotState:
        """Get current robot state"""
        return self.state
    
    def display_leg_positions(self):
        """Display the current foot positions for all legs"""
        print("Current Leg Positions:")
        for leg_id in LEG_LABELS:
            pos = self.state.foot_positions[leg_id]
            print(f"{leg_id} - X: {pos[0]:.3f}, Y: {pos[1]:.3f}, Z: {pos[2]:.3f}")


def main():
    # Create robot instance
    robot = QuadrupedRobot(GaitType.TROT)
    
    try:
        print("Starting robot movement sequence...")
        
        # Move forward 1 meter
        distance = 1.0
        steps = int(distance / gait_params.STEP_LENGTH)
        print(f"Moving forward {distance} meters...")
        
        for _ in range(steps):
            robot.update()
            robot.move_forward(gait_params.STEP_LENGTH)
            robot.display_leg_positions()
            time.sleep(1.0 / gait_params.STEP_FREQUENCY)
        
        print("Forward movement complete.")
        print(f"Current Position - X: {robot.state.position[0]:.3f}, Y: {robot.state.position[1]:.3f}, Z: {robot.state.position[2]:.3f}")
        
        # Turn 90 degrees
        angle = np.pi / 2
        print(f"Turning {np.degrees(angle)} degrees...")
        
        robot.turn(angle)
        robot.display_leg_positions()
        
        print("Turn complete.")
        print(f"Current Orientation - Roll: {robot.state.orientation[0]:.3f}, Pitch: {robot.state.orientation[1]:.3f}, Yaw: {robot.state.orientation[2]:.3f}")
        
        # Move backward 0.5 meters
        distance = 0.5
        steps = int(distance / gait_params.STEP_LENGTH)
        print(f"Moving backward {distance} meters...")
        
        for _ in range(steps):
            robot.update()
            robot.move_backward(gait_params.STEP_LENGTH)
            robot.display_leg_positions()
            time.sleep(1.0 / gait_params.STEP_FREQUENCY)
        
        print("Backward movement complete.")
        print(f"Current Position - X: {robot.state.position[0]:.3f}, Y: {robot.state.position[1]:.3f}, Z: {robot.state.position[2]:.3f}")
        
    except KeyboardInterrupt:
        print("\nStopping robot...")
    
    except Exception as e:
        print(f"Error occurred: {e}")
    
    finally:
        print("Robot shutdown complete.")


if __name__ == "__main__":
    main()