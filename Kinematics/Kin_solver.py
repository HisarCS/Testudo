import numpy as np

class QuadrupedMovementSolver:
    def __init__(self, L1=0.06, L2=0.04, step_length=0.1, step_height=0.02):
        """
        Initialize quadruped parameters for movement.
        :param L1: Upper leg length (meters)
        :param L2: Lower leg length (meters)
        :param step_length: Length of each step in meters
        :param step_height: Maximum height of the foot during a step
        """
        self.L1 = L1
        self.L2 = L2
        self.step_length = step_length
        self.step_height = step_height
        self.legs = ['FL', 'FR', 'RL', 'RR']  # Front Left, Front Right, Rear Left, Rear Right
    
    def inverse_kinematics(self, x, y):
        """
        Compute joint angles given a desired foot position.
        :param x: Desired x position of foot
        :param y: Desired y position of foot
        :return: (theta1, theta2) joint angles in radians
        """
        D = (x**2 + y**2 - self.L1**2 - self.L2**2) / (2 * self.L1 * self.L2)
        if np.abs(D) > 1:
            return None, None  # Return None values if the position is unreachable
        theta2 = np.arccos(D)
        theta1 = np.arctan2(y, x) - np.arctan2(self.L2 * np.sin(theta2), self.L1 + self.L2 * np.cos(theta2))
        return theta1, theta2
    
    def generate_step_trajectory(self):
        """
        Generate footstep trajectory for smooth walking motion.
        :return: List of (x, y) foot positions with corresponding joint angles
        """
        steps = 10  # Number of discrete positions in each step
        x_traj = np.linspace(-self.step_length / 2, self.step_length / 2, steps)
        y_traj = self.step_height * np.sin(np.pi * (x_traj + self.step_length / 2) / self.step_length)
        step_data = []
        
        for x, y in zip(x_traj, y_traj):
            theta1, theta2 = self.inverse_kinematics(x, y)
            step_data.append((x, y, theta1, theta2))
        
        return step_data
    
    def move_forward(self, distance):
        """
        Generate step cycles to move the quadruped forward.
        :param distance: Total distance to move forward in meters
        :return: List of step sequences for all legs with joint angles
        """
        num_steps = int(distance / self.step_length)
        all_steps = []
        
        for step in range(num_steps):
            step_positions = self.generate_step_trajectory()
            step_data = {leg: step_positions for leg in self.legs}
            all_steps.append(step_data)
        
        return all_steps

# Example usage
if __name__ == "__main__":
    quadruped = QuadrupedMovementSolver()
    total_distance = 20  
    movement_plan = quadruped.move_forward(total_distance)
    
    print(f"Executing movement for {total_distance} meters with step length {quadruped.step_length} meters:")
    for i, step in enumerate(movement_plan):
        print(f"Step {i+1}:")
        for leg, positions in step.items():
            print(f"  {leg} positions and angles:")
            for pos in positions:
                x, y, theta1, theta2 = pos
                if theta1 is None or theta2 is None:
                    print(f"    Foot Position: ({x:.3f}, {y:.3f}) | Angles: Out of reach")
                else:
                    print(f"    Foot Position: ({x:.3f}, {y:.3f}) | Angles: Theta1 = {theta1:.3f} rad, Theta2 = {theta2:.3f} rad")
