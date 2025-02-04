from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional
import numpy as np

class LegID(Enum):
    FL = 1
    FR = 2
    BL = 3
    BR = 4

class RobotMode(Enum):
    STANDING = auto()
    WALKING = auto()
    TRANSITIONING = auto()
    ERROR = auto()

class GaitType(Enum):
    TROT = auto()
    WALK = auto()
    BOUND = auto()

@dataclass
class ServoConfig:
    min_angle: float = -90.0
    max_angle: float = 90.0
    max_speed: float = 0.16
    max_torque: float = 15.0
    deadband: float = 1.0
    pwm_min: int = 500
    pwm_max: int = 2500
    pwm_freq: int = 50

@dataclass
class LegConfig:
    upper_length: float = 75.0
    lower_length: float = 75.0
    min_inner_angle: float = 15.0
    max_inner_angle: float = 150.0
    max_extension: float = 145.0
    min_extension: float = 60.0
    mass: float = 0.1
    upper_mass_center: float = 37.5
    lower_mass_center: float = 37.5
    upper_inertia: float = 0.0001
    lower_inertia: float = 0.0001
    foot_friction: float = 0.8
    servo_upper: ServoConfig = field(default_factory=lambda: ServoConfig(-90, 90))
    servo_lower: ServoConfig = field(default_factory=lambda: ServoConfig(0, 180))

@dataclass
class GaitConfig:
    step_height: float = 40.0
    step_length: float = 80.0
    stance_height: float = -200.0  # Adjusted stance height
    duty_factor: float = 0.6  # Adjusted duty factor
    stance_time: float = 0.3  # Adjusted stance time
    swing_time: float = 0.2  # Adjusted swing time
    transition_time: float = 0.2
    clearance_time: float = 0.1
    stability_margin: float = 30.0
    max_velocity: float = 0.5
    phase_offset: Dict[LegID, float] = field(default_factory=lambda: {
        LegID.FL: 0.0,
        LegID.BR: 0.0,
        LegID.FR: 0.5,
        LegID.BL: 0.5
    })

@dataclass
class RobotConfig:
    body_length: float = 240.0
    body_width: float = 120.0
    body_height: float = 200.0
    body_mass: float = 0.8
    body_inertia: Tuple[float, float, float] = (0.001, 0.002, 0.003)
    gravity: float = 9.81
    dt: float = 0.01
    control_freq: float = 100
    leg: LegConfig = field(default_factory=LegConfig)
    gait: GaitConfig = field(default_factory=GaitConfig)

    def get_leg_offset(self, leg_id: LegID) -> np.ndarray:
        x = self.body_length / 2.0
        y = self.body_width / 2.0
        
        if leg_id in [LegID.FL, LegID.FR]:
            x *= 1
        else:
            x *= -1
            
        if leg_id in [LegID.FL, LegID.BL]:
            y *= 1
        else:
            y *= -1
            
        return np.array([x, y, 0])