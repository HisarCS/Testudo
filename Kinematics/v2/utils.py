import numpy as np
from typing import List, Dict, Tuple
from core import RobotState

def rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """Convert euler angles to rotation matrix"""
    # Roll (X)
    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])
    
    # Pitch (Y)
    Ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])
    
    # Yaw (Z)
    Rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])
    
    return Rz @ Ry @ Rx

def euler_angles(R: np.ndarray) -> Tuple[float, float, float]:
    """Extract euler angles from rotation matrix"""
    pitch = np.arcsin(-R[2, 0])
    
    if np.cos(pitch) > 1e-6:
        roll = np.arctan2(R[2, 1], R[2, 2])
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:
        roll = 0.0
        yaw = np.arctan2(-R[0, 1], R[1, 1])
        
    return roll, pitch, yaw

def normalize_angle(angle: float) -> float:
    """Normalize angle to [-pi, pi]"""
    return (angle + np.pi) % (2 * np.pi) - np.pi

def create_transform(pos: np.ndarray, rot: np.ndarray) -> np.ndarray:
    """Create 4x4 homogeneous transformation matrix"""
    T = np.eye(4)
    T[:3, :3] = rot
    T[:3, 3] = pos
    return T

def interpolate(start: np.ndarray, end: np.ndarray, t: float) -> np.ndarray:
    """Linear interpolation between two points
    Args:
        start: Starting point
        end: Ending point
        t: Interpolation factor [0, 1]
    """
    return start + t * (end - start)

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))

def distance(p1: np.ndarray, p2: np.ndarray) -> float:
    """Compute Euclidean distance between points"""
    return np.linalg.norm(p2 - p1)

def project_to_plane(point: np.ndarray, plane_normal: np.ndarray) -> np.ndarray:
    """Project point onto plane defined by normal vector"""
    d = np.dot(point, plane_normal)
    return point - d * plane_normal