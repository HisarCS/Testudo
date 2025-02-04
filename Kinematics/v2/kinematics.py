import numpy as np
from typing import Tuple, Optional, Dict
from core import physical_params, RobotState, LEG_LABELS

def forward_kinematics(theta_hip: float, theta_knee: float) -> np.ndarray:
    """
    Calculate foot position in leg frame given joint angles
    Returns: position vector [x, y, z] in leg frame
    """
    L1, L2 = physical_params.L1, physical_params.L2
    
    # x position
    x = L1 * np.cos(theta_hip) + L2 * np.cos(theta_hip + theta_knee)
    
    # z position (negative because down is positive)
    z = -(L1 * np.sin(theta_hip) + L2 * np.sin(theta_hip + theta_knee))
    
    return np.array([x, 0, z])

def inverse_kinematics(x: float, y: float, z: float) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate joint angles for given foot position in leg frame
    Returns: (theta_hip, theta_knee) or (None, None) if position unreachable
    """
    L1, L2 = physical_params.L1, physical_params.L2
    
    # Convert to 2D problem (ignore y)
    R = np.sqrt(x**2 + z**2)
    
    # Check if point is reachable
    if R > L1 + L2 or R < abs(L1 - L2):
        return None, None
        
    # Calculate knee angle using cosine law
    cos_knee = (R**2 - L1**2 - L2**2) / (2 * L1 * L2)
    if abs(cos_knee) > 1:
        return None, None
        
    theta_knee = -np.arccos(cos_knee)  # Negative for "knee forward" configuration
    
    # Calculate hip angle
    theta_hip = np.arctan2(-z, x) - np.arctan2(L2 * np.sin(theta_knee),
                                              L1 + L2 * np.cos(theta_knee))
    
    # Check joint limits
    if not check_joint_limits(theta_hip, theta_knee):
        return None, None
        
    return theta_hip, theta_knee

def check_joint_limits(theta_hip: float, theta_knee: float) -> bool:
    """Check if joint angles are within allowed range"""
    return (physical_params.MIN_HIP_ANGLE <= theta_hip <= physical_params.MAX_HIP_ANGLE and
            physical_params.MIN_KNEE_ANGLE <= theta_knee <= physical_params.MAX_KNEE_ANGLE)

def leg_to_body_frame(pos_leg: np.ndarray, leg_id: str, robot_state: RobotState) -> np.ndarray:
    """Transform position from leg frame to body frame"""
    from .core import get_leg_origins
    
    # Get leg origin in body frame
    leg_origin = get_leg_origins()[leg_id]
    
    # Simple translation (assuming no body rotation for now)
    return leg_origin + pos_leg

def body_to_world_frame(pos_body: np.ndarray, robot_state: RobotState) -> np.ndarray:
    """Transform position from body frame to world frame"""
    # Get rotation matrix from euler angles
    roll, pitch, yaw = robot_state.orientation
    R = euler_to_rotation_matrix(roll, pitch, yaw)
    
    # Apply rotation and translation
    return R @ pos_body + robot_state.position

def euler_to_rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """Convert euler angles to rotation matrix"""
    # Roll
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(roll), -np.sin(roll)],
                   [0, np.sin(roll), np.cos(roll)]])
    
    # Pitch
    Ry = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                   [0, 1, 0],
                   [-np.sin(pitch), 0, np.cos(pitch)]])
    
    # Yaw
    Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                   [np.sin(yaw), np.cos(yaw), 0],
                   [0, 0, 1]])
    
    # Combined rotation
    return Rz @ Ry @ Rx

def compute_jacobian(theta_hip: float, theta_knee: float) -> np.ndarray:
    """
    Compute Jacobian matrix for leg
    Returns: 2x2 Jacobian matrix relating joint velocities to foot velocities
    """
    L1, L2 = physical_params.L1, physical_params.L2
    
    J = np.zeros((2, 2))
    
    # For x velocity
    J[0, 0] = -L1 * np.sin(theta_hip) - L2 * np.sin(theta_hip + theta_knee)
    J[0, 1] = -L2 * np.sin(theta_hip + theta_knee)
    
    # For z velocity
    J[1, 0] = -L1 * np.cos(theta_hip) - L2 * np.cos(theta_hip + theta_knee)
    J[1, 1] = -L2 * np.cos(theta_hip + theta_knee)
    
    return J