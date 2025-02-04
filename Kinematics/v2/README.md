# Quadruped Robot Simulation & Control System Documentation

## Overview
This project implements a quadruped robot simulation and control system. It includes physics-based modeling, kinematics, dynamics, and gait generation to simulate the movement of a four-legged robot. The code is modular, separating core functionality, movement calculations, and physical properties.

---

## 1. `__init__.py`
### Purpose:
- Serves as a module initializer.
- Imports essential components from different modules.

### Key Imports:
- **`core.py`**: Defines robot state, physical parameters, and gaits.
- **`kinematics.py`**: Computes joint angles and transformations.
- **`dynamics.py`**: Handles physics-based computations.
- **`gaits.py`**: Manages gait cycles.

---

## 2. `core.py`
### Purpose:
Defines fundamental properties of the robot, including physical parameters and gait settings.

### Key Components:
- **`GaitType`**: Enum defining gaits (`TROT`, `WALK`, `BOUND`).
- **`PhysicalParams`**:
  - Leg lengths, body dimensions, mass properties.
- **`RobotState`**:
  - Tracks joint angles, velocities, and foot contacts.

---

## 3. `dynamics.py`
### Purpose:
Handles physics-based calculations for the quadruped robot.

### Key Functions:
- **`compute_mass_matrix(robot_state)`**:
  - Computes the system's 6x6 mass matrix.
- **`compute_gravity_forces(robot_state)`**:
  - Computes gravitational effects on the robot.
- **`compute_centroidal_momentum(robot_state)`**:
  - Determines overall momentum.
- **`compute_ground_reaction_forces(robot_state)`**:
  - Computes forces exerted by the ground on each leg.

---

## 4. `gaits.py`
### Purpose:
Defines gait cycle planning and execution.

### Key Components:
- **`GaitGenerator`**:
  - Manages gait transitions.
  - Uses predefined phase offsets for movement.
  - Controls stance and swing heights.

---

## 5. `kinematics.py`
### Purpose:
Handles movement calculations, including joint positioning and transformations.

### Key Functions:
- **`forward_kinematics(theta_hip, theta_knee)`**:
  - Computes foot position from joint angles.
- **`inverse_kinematics(target_position)`**:
  - Computes required joint angles for a given foot position.
- **`leg_to_body_frame()`** & **`body_to_world_frame()`**:
  - Converts positions between different reference frames.

---

## 6. `main.py`
### Purpose:
Entry point for robot control and simulation.

### Key Components:
- **`QuadrupedRobot`**:
  - Initializes robot state.
  - Controls gait cycles.
  - Integrates kinematics and dynamics for movement.

---

## 7. `utils.py`
### Purpose:
Provides helper functions for numerical and transformation computations.

### Key Functions:
- **`rotation_matrix(roll, pitch, yaw)`**:
  - Converts Euler angles into a rotation matrix.

---

## Physics Behind the Simulation
### Mass and Force Calculations
- The **mass matrix** represents the system's inertia. Each component of the quadruped contributes to this matrix based on its mass, position, and orientation in the reference frame. The total inertia is computed by integrating the mass distribution across all limbs and joints, ensuring accurate torque calculations.
- **Gravity forces** are calculated for each limb individually. The gravitational force applied to each segment depends on its mass and the center of gravity. The sum of these individual forces determines the overall gravitational effect on the system, which influences balance and stability.
- **Ground reaction forces (GRF)** are dynamically adjusted based on foot contact conditions. These forces are determined using a contact model that accounts for the robot’s velocity, terrain friction, and normal forces. Unequal distribution of these forces can cause instability, requiring real-time corrections.

### Kinematics & Motion Planning
- **Forward kinematics** computes the position of the robot’s feet based on its joint angles. This involves applying a series of rotational and translational transformations for each limb segment, ensuring accurate foot placement in the global frame.
- **Inverse kinematics** determines the joint angles required to position the foot at a given target location. This process involves solving nonlinear equations, which can be achieved using numerical methods such as Newton-Raphson iteration or optimization techniques.
- The **Jacobian matrix** is essential for velocity control. It maps joint velocity to foot velocity and is used to ensure smooth movements. Additionally, it assists in computing force transmission, allowing precise torque control at the joints.

### Gait Control & Stability
- A quadruped’s gait cycle consists of alternating stance and swing phases:
  - **Stance Phase:** The leg is in contact with the ground, exerting force to support and propel the robot.
  - **Swing Phase:** The leg moves forward, preparing for the next contact with the ground.
- **Zero Moment Point (ZMP) Criterion** ensures that the net moment of all forces remains within the support polygon. If the ZMP moves outside this region, the robot becomes unstable and corrective adjustments must be made.
- **Raibert Heuristic** dynamically adjusts foot placement by predicting the necessary step length based on velocity and terrain conditions. This helps the robot maintain speed and adaptability across different environments.
- **Dynamic Stability Control** continuously adjusts the timing of foot placement and weight distribution to compensate for uneven terrain and external disturbances. This is crucial for traversing slopes, stepping over obstacles, and handling external forces.

---

## Summary
This quadruped robot control system provides a structured approach to simulate and control a four-legged robotic platform. The modular approach allows for easy integration of new gaits, enhanced kinematics, and optimized dynamics computations. Future improvements could focus on:
- **Optimizing numerical computations for real-time performance**.
- **Integrating machine learning for adaptive gait generation**.
- **Enhancing the physics engine for better accuracy, particularly in response to dynamic environmental conditions**.

---

## Next Steps
Would you like additional explanations, optimizations, or new gait types integrated? Let me know how I can assist further!
