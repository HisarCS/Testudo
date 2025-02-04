import numpy as np
from config import RobotConfig, LegConfig
from typing import Optional, Tuple

class LegKinematics:
    def __init__(self, config: LegConfig):
        self.config = config
        self.l1 = config.upper_length
        self.l2 = config.lower_length
        
    def inverse_kinematics(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        l1_sq = self.l1 * self.l1
        l2_sq = self.l2 * self.l2
        r_sq = x * x + y * y
        
        if r_sq > (self.l1 + self.l2) * (self.l1 + self.l2):
            return None
            
        if r_sq < (self.l1 - self.l2) * (self.l1 - self.l2):
            return None
            
        D = (r_sq - l1_sq - l2_sq) / (2 * self.l1 * self.l2)
        if abs(D) > 1:
            return None
            
        theta2 = np.arccos(D)
        theta1 = np.arctan2(y, x) - np.arctan2(self.l2 * np.sin(theta2),
                                              self.l1 + self.l2 * np.cos(theta2))
        
        angles = np.degrees([theta1, theta2])
        if not self._validate_angles(angles[0], angles[1]):
            return None
            
        return angles[0], angles[1]
        
    def forward_kinematics(self, theta1: float, theta2: float) -> Tuple[float, float]:
        theta1_rad = np.radians(theta1)
        theta2_rad = np.radians(theta2)
        
        x = (self.l1 * np.cos(theta1_rad) + 
             self.l2 * np.cos(theta1_rad + theta2_rad))
        y = (self.l1 * np.sin(theta1_rad) + 
             self.l2 * np.sin(theta1_rad + theta2_rad))
             
        return x, y
        
    def _validate_angles(self, theta1: float, theta2: float) -> bool:
        if not (self.config.servo_upper.min_angle <= theta1 <= self.config.servo_upper.max_angle):
            return False
            
        if not (self.config.servo_lower.min_angle <= theta2 <= self.config.servo_lower.max_angle):
            return False
            
        inner_angle = 180 - abs(theta2)
        if not (self.config.min_inner_angle <= inner_angle <= self.config.max_inner_angle):
            return False
            
        pos = self.forward_kinematics(theta1, theta2)
        extension = np.sqrt(pos[0]*pos[0] + pos[1]*pos[1])
        
        if not (self.config.min_extension <= extension <= self.config.max_extension):
            return False
            
        return True
        
    def compute_jacobian(self, theta1: float, theta2: float) -> np.ndarray:
        t1 = np.radians(theta1)
        t2 = np.radians(theta2)
        
        J = np.zeros((2, 2))
        
        J[0,0] = -self.l1*np.sin(t1) - self.l2*np.sin(t1 + t2)
        J[0,1] = -self.l2*np.sin(t1 + t2)
        J[1,0] = self.l1*np.cos(t1) + self.l2*np.cos(t1 + t2)
        J[1,1] = self.l2*np.cos(t1 + t2)
        
        return J
        
    def compute_torques(self, theta1: float, theta2: float, fx: float, fy: float) -> Tuple[float, float]:
        J = self.compute_jacobian(theta1, theta2)
        F = np.array([fx, fy])
        tau = np.dot(J.T, F)
        
        tau1 = tau[0] + self._compute_gravity_torque(theta1, theta2, 0)
        tau2 = tau[1] + self._compute_gravity_torque(theta1, theta2, 1)
        
        return tau1, tau2
        
    def _compute_gravity_torque(self, theta1: float, theta2: float, joint: int) -> float:
        g = 9.81
        m1 = self.config.mass/2
        m2 = self.config.mass/2
        
        t1 = np.radians(theta1)
        t2 = np.radians(theta2)
        
        if joint == 0:
            tau = (-m1 * g * self.config.upper_mass_center * np.cos(t1) -
                   m2 * g * (self.l1 * np.cos(t1) + 
                            self.config.lower_mass_center * np.cos(t1 + t2)))
        else:
            tau = -m2 * g * self.config.lower_mass_center * np.cos(t1 + t2)
            
        return tau

class QuadrupedKinematics:
    def __init__(self, config: RobotConfig):
        self.config = config
        self.leg_kinematics = LegKinematics(config.leg)
        
    def body_to_leg(self, leg_id, x: float, y: float, z: float) -> Tuple[float, float]:
        offset = self.config.get_leg_offset(leg_id)
        leg_x = x - offset[0]
        leg_y = y - offset[1]
        
        r = np.sqrt(leg_x*leg_x + leg_y*leg_y)
        z_adj = z + offset[2]
        
        return r, z_adj
        
    def leg_angles_to_world(self, leg_id, angles: Tuple[float, float]) -> np.ndarray:
        foot_pos = self.leg_kinematics.forward_kinematics(*angles)
        offset = self.config.get_leg_offset(leg_id)
        
        world_pos = np.array([
            foot_pos[0] + offset[0],
            foot_pos[1] + offset[1],
            0.0
        ])
        
        return world_pos