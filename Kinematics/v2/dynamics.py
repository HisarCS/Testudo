import numpy as np
from typing import Dict, List, Tuple
from core import physical_params, RobotState, LEG_LABELS
from kinematics import compute_jacobian

def compute_mass_matrix(robot_state: RobotState) -> np.ndarray:
    """
    Compute the system mass matrix
    Returns: 6x6 mass matrix for the full robot
    """
    # Initialize mass matrix
    M = np.zeros((6, 6))
    
    # Add body mass contribution
    M[0:3, 0:3] = physical_params.BODY_MASS * np.eye(3)
    
    # Add leg mass contributions (simplified)
    for leg_id in LEG_LABELS:
        angles = robot_state.joint_angles[leg_id]
        J = compute_jacobian(*angles)
        M_leg = physical_params.LEG_MASS * np.eye(2)
        M[:2, :2] += J.T @ M_leg @ J
    
    return M

def compute_gravity_forces(robot_state: RobotState) -> Dict[str, np.ndarray]:
    """
    Compute gravity forces in joint space
    Returns: Dictionary of gravity forces for each leg
    """
    g = 9.81  # gravity constant
    forces = {}
    
    for leg_id in LEG_LABELS:
        theta_hip, theta_knee = robot_state.joint_angles[leg_id]
        
        # Simplified model: point masses at leg centers
        hip_force = -physical_params.LEG_MASS * g * physical_params.L1 * np.sin(theta_hip) / 2
        knee_force = -physical_params.LEG_MASS * g * physical_params.L2 * np.sin(theta_hip + theta_knee) / 2
        
        forces[leg_id] = np.array([hip_force, knee_force])
    
    return forces

def compute_centroidal_momentum(robot_state: RobotState) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute linear and angular momentum about the center of mass
    Returns: (linear_momentum, angular_momentum)
    """
    linear_momentum = physical_params.TOTAL_MASS * robot_state.velocity
    
    # Compute angular momentum
    angular_momentum = np.zeros(3)
    com = compute_com_position(robot_state)
    
    for leg_id in LEG_LABELS:
        r = robot_state.foot_positions[leg_id] - com
        v = robot_state.velocity  # Simplified: using body velocity
        angular_momentum += np.cross(r, physical_params.LEG_MASS * v)
    
    return linear_momentum, angular_momentum

def compute_ground_reaction_forces(robot_state: RobotState, 
                                 stance_legs: List[str]) -> Dict[str, np.ndarray]:
    """
    Estimate ground reaction forces for legs in stance
    Returns: Dictionary mapping leg_id to force vector
    """
    forces = {}
    num_stance_legs = len(stance_legs)
    
    if num_stance_legs == 0:
        return {leg: np.zeros(3) for leg in LEG_LABELS}
    
    # Distribute robot weight among stance legs
    force_magnitude = physical_params.TOTAL_MASS * 9.81 / num_stance_legs
    
    for leg_id in LEG_LABELS:
        if leg_id in stance_legs:
            # Vertical force only for simplicity
            forces[leg_id] = np.array([0, 0, force_magnitude])
        else:
            forces[leg_id] = np.zeros(3)
    
    return forces

def compute_joint_torques(robot_state: RobotState, 
                         ground_forces: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Compute required joint torques given ground reaction forces
    Returns: Dictionary mapping leg_id to torque vector
    """
    torques = {}
    gravity_forces = compute_gravity_forces(robot_state)
    
    for leg_id in LEG_LABELS:
        # Get leg Jacobian
        theta_hip, theta_knee = robot_state.joint_angles[leg_id]
        J = compute_jacobian(theta_hip, theta_knee)
        
        # Transform ground force to joint torques
        force = ground_forces[leg_id][:2]  # Only x,z components
        torques[leg_id] = J.T @ force
        
        # Add gravity compensation
        torques[leg_id] += gravity_forces[leg_id]
    
    return torques

def compute_com_position(robot_state: RobotState) -> np.ndarray:
    """
    Compute center of mass position
    Returns: COM position vector [x, y, z]
    """
    total_mass = physical_params.TOTAL_MASS
    com = physical_params.BODY_MASS * robot_state.position
    
    # Add leg contributions
    for leg_id in LEG_LABELS:
        # Approximate leg COM as midpoint between hip and foot
        hip_pos = robot_state.position + robot_state.foot_positions[leg_id]
        foot_pos = robot_state.foot_positions[leg_id]
        leg_com = (hip_pos + foot_pos) / 2
        com += physical_params.LEG_MASS * leg_com
    
    return com / total_mass

def compute_inertia_matrix(robot_state: RobotState) -> np.ndarray:
    """
    Compute inertia matrix about COM
    Returns: 3x3 inertia matrix
    """
    # Simplified inertia matrix using parallel axis theorem
    I = np.zeros((3, 3))
    com = compute_com_position(robot_state)
    
    # Body contribution (approximated as rectangular prism)
    l, w, h = physical_params.BODY_LENGTH, physical_params.BODY_WIDTH, 0.05  # height approximated
    I[0,0] = physical_params.BODY_MASS * (w**2 + h**2) / 12  # Ixx
    I[1,1] = physical_params.BODY_MASS * (l**2 + h**2) / 12  # Iyy
    I[2,2] = physical_params.BODY_MASS * (l**2 + w**2) / 12  # Izz
    
    # Leg contributions (simplified as point masses)
    for leg_id in LEG_LABELS:
        r = robot_state.foot_positions[leg_id] - com
        r_matrix = np.array([
            [r[1]**2 + r[2]**2, -r[0]*r[1], -r[0]*r[2]],
            [-r[0]*r[1], r[0]**2 + r[2]**2, -r[1]*r[2]],
            [-r[0]*r[2], -r[1]*r[2], r[0]**2 + r[1]**2]
        ])
        I += physical_params.LEG_MASS * r_matrix
    
    return I