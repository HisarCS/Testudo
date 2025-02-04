from config import RobotConfig, LegID, RobotMode, GaitType
from gait_controller import GaitController
import numpy as np
import time
from typing import Dict

class QuadrupedCalculator:
    def __init__(self, config: RobotConfig):
        self.config = config
        self.gait_controller = GaitController(config)
        self.last_command_time = time.time()
        self.step_counter = 0

    def update(self):
        self.gait_controller.update()
        leg_states = self.gait_controller.get_leg_states()
        body_state = self.gait_controller.get_body_state()
        self._print_state(leg_states, body_state)
        self.step_counter += 1

    def set_velocity(self, vx: float, vy: float, yaw_rate: float):
        self.last_command_time = time.time()
        velocity = np.array([vx, vy, 0.0])
        if self.gait_controller.mode == RobotMode.STANDING:
            self.gait_controller.start_walking(velocity, yaw_rate)
        else:
            self.gait_controller.velocity = velocity
            self.gait_controller.yaw_rate = yaw_rate

    def set_height(self, height: float):
        self.gait_controller.set_body_height(height)

    def set_gait(self, gait_type: GaitType):
        self.gait_controller.set_gait(gait_type)

    def _print_state(self, leg_states: Dict, body_state: Dict):
        print(f"\nStep {self.step_counter} ===========================")
        print(f"Robot State:")
        print(f"Mode: {body_state['mode']}")
        print(f"Phase: {body_state['phase']:.3f}")
        print(f"Velocity: [{body_state['velocity'][0]:.3f}, {body_state['velocity'][1]:.3f}, {body_state['velocity'][2]:.3f}]")
        print(f"Yaw Rate: {body_state['yaw_rate']:.3f}")
        print(f"Body Height: {body_state['height']:.3f}")
        print("\nLeg States:")
        for leg_id, state in leg_states.items():
            angles = state['angles']
            torques = state['torques']
            print(f"{leg_id.name}:")
            print(f"  Angles: [{angles[0]:.2f}°, {angles[1]:.2f}°]")
            print(f"  Torques: [{torques[0]:.2f}, {torques[1]:.2f}] N⋅m")
            print(f"  Contact: {state['contact']}")

def main():
    config = RobotConfig()
    calculator = QuadrupedCalculator(config)
    update_interval = 0.1  # 100ms between updates

    print("Starting calculation simulation")

    # Set the desired walking distance and velocity
    distance = 1000.0  # millimeters
    velocity = 300.0  # mm/s

    # Calculate the number of steps needed to cover the distance
    steps = int(distance / (velocity * update_interval))

    # Set the velocity and start walking
    calculator.set_velocity(velocity, 0.0, 0.0)

    # Simulate the walking motion
    for _ in range(steps):
        calculator.update()
        time.sleep(update_interval)

    # Stop the robot after reaching the desired distance
    calculator.set_velocity(0.0, 0.0, 0.0)

    print("Calculation simulation completed.")

if __name__ == "__main__":
    main()