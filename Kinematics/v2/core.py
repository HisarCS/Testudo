from dataclasses import dataclass
from enum import Enum
import numpy as np
from typing import Dict, List, Tuple, Optional

class GaitType(Enum):
    TROT = "trot"
    WALK = "walk"
    BOUND = "bound"

@dataclass
class PhysicalParams:
    # Leg lengths (meters)
    L1: float = 0.10  # Upper leg length
    L2: float = 0.10  # Lower leg length
    
    # Body dimensions (meters)
    BODY_LENGTH: float = 0.30
    BODY_WIDTH: float = 0.15
    
    # Mass properties (kg)
    TOTAL_MASS: float = 12.0
    LEG_MASS: float = 0.5
    BODY_MASS: float = 10.0
    
    # Joint limits (radians)
    MAX_HIP_ANGLE: float = np.pi/2
    MIN_HIP_ANGLE: float = -np.pi/2
    MAX_KNEE_ANGLE: float = 0
    MIN_KNEE_ANGLE: float = -2*np.pi/3

@dataclass
class GaitParams:
    # Gait parameters
    STEP_LENGTH: float = 0.15
    STEP_HEIGHT: float = 0.03
    STEP_VELOCITY: float = 0.5
    GROUND_CLEARANCE: float = 0.02
    STEP_FREQUENCY: float = 2.0
    DUTY_FACTOR: float = 0.5
    STEP_POINTS: int = 10

@dataclass
class RobotState:
    position: np.ndarray  # [x, y, z]
    orientation: np.ndarray  # [roll, pitch, yaw]
    velocity: np.ndarray  # [vx, vy, vz]
    angular_velocity: np.ndarray  # [wx, wy, wz]
    foot_positions: Dict[str, np.ndarray]  # leg_id -> [x, y, z]
    joint_angles: Dict[str, Tuple[float, float]]  # leg_id -> (hip, knee)

# Initialize default parameters
physical_params = PhysicalParams()
gait_params = GaitParams()

# Leg labels and their positions in body frame
LEG_LABELS = ['FL', 'FR', 'RL', 'RR']  # Front-Left, Front-Right, Rear-Left, Rear-Right

def get_leg_origins() -> Dict[str, np.ndarray]:
    """Get the hip joint positions in body frame for each leg"""
    half_length = physical_params.BODY_LENGTH / 2.0
    half_width = physical_params.BODY_WIDTH / 2.0
    
    return {
        'FL': np.array([+half_length, +half_width, 0.0]),
        'FR': np.array([+half_length, -half_width, 0.0]),
        'RL': np.array([-half_length, +half_width, 0.0]),
        'RR': np.array([-half_length, -half_width, 0.0])
    }

def get_default_stance() -> Dict[str, np.ndarray]:
    """Get default foot positions in body frame"""
    leg_origins = get_leg_origins()
    stance_height = -(physical_params.L1 + physical_params.L2) * 0.7
    
    return {
        leg: origin + np.array([0, 0, stance_height])
        for leg, origin in leg_origins.items()
    }

# Gait phase offsets for different gaits
GAIT_PHASE_OFFSETS = {
    GaitType.TROT: {
        'FL': 0.0,
        'RR': 0.0,
        'FR': 0.5,
        'RL': 0.5
    },
    GaitType.WALK: {
        'FL': 0.0,
        'FR': 0.25,
        'RL': 0.5,
        'RR': 0.75
    },
    GaitType.BOUND: {
        'FL': 0.0,
        'FR': 0.0,
        'RL': 0.5,
        'RR': 0.5
    }
}