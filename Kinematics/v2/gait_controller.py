import numpy as np
from typing import Dict, Tuple
from config import RobotConfig, LegID, RobotMode, GaitType
from leg_controller import LegController
from stability_controller import StabilityController
import time

class GaitController:
    def __init__(self, config: RobotConfig):
        self.config = config
        self.mode = RobotMode.STANDING
        self.phase = 0.0
        self.gait_type = GaitType.TROT
        self.velocity = np.zeros(3)
        self.target_velocity = np.zeros(3)
        self.yaw_rate = 0.0
        self.target_yaw_rate = 0.0
        self.body_height = config.gait.stance_height
        self.target_height = config.gait.stance_height
        self.transition_start_time = 0.0
        self.last_update_time = time.time()
        
        self.max_acceleration = 2.0  # m/s^2
        self.max_yaw_acceleration = 4.0  # rad/s^2
        
        self.leg_controllers = {
            leg: LegController(leg, config) for leg in LegID
        }
        self.stability_controller = StabilityController(config)
        
    def update(self):
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time
        
        self._update_velocity_smooth(dt)
        leg_states = self._update_leg_states(dt)
                     
        is_stable = self.stability_controller.update(leg_states)
        
        if not is_stable and self.mode == RobotMode.WALKING:
            self._handle_instability()
            return
            
        if self.mode == RobotMode.WALKING:
            self._update_walking_phase(dt)
            body_velocity = self._compute_body_velocity()
            
            for leg_id, controller in self.leg_controllers.items():
                leg_velocity = self._compute_leg_velocity(leg_id, body_velocity)
                controller.update(self.phase, leg_velocity)
                
        elif self.mode == RobotMode.STANDING:
            self._update_standing()
                
        elif self.mode == RobotMode.TRANSITIONING:
            if self._update_transition(dt):
                self.mode = RobotMode.WALKING
                self.phase = 0.0

    def _update_velocity_smooth(self, dt: float):
        # Smooth velocity changes
        vel_diff = self.target_velocity - self.velocity
        vel_change = np.clip(
            vel_diff, 
            -self.max_acceleration * dt,
            self.max_acceleration * dt
        )
        self.velocity += vel_change
        
        # Smooth yaw rate changes
        yaw_diff = self.target_yaw_rate - self.yaw_rate
        yaw_change = np.clip(
            yaw_diff,
            -self.max_yaw_acceleration * dt,
            self.max_yaw_acceleration * dt
        )
        self.yaw_rate += yaw_change

    def _update_leg_states(self, dt: float) -> Dict[LegID, Dict]:
        states = {}
        for leg_id, controller in self.leg_controllers.items():
            state = controller.get_state()
            states[leg_id] = {
                'angles': state.current_angles.tolist(),
                'torques': state.current_torque.tolist(),
                'contact': state.in_contact,
                'position': controller.kinematics.forward_kinematics(*state.current_angles)
            }
        return states

    def _update_walking_phase(self, dt: float):
        cycle_time = self.config.gait.stance_time + self.config.gait.swing_time
        self.phase += dt / cycle_time
        if self.phase >= 1.0:
            self.phase -= 1.0
            
    def _update_standing(self):
        height = self.config.gait.stance_height
        for controller in self.leg_controllers.values():
            default_pos = np.array([0.0, height])
            angles = controller.kinematics.inverse_kinematics(*default_pos)
            if angles is not None:
                controller.state.target_angles = np.array(angles)
                controller.update(0.0, np.zeros(3))
                
    def _update_transition(self, dt: float) -> bool:
        elapsed = time.time() - self.transition_start_time
        progress = elapsed / self.config.gait.transition_time
        
        if progress >= 1.0:
            return True
        
        # Use a more explicit leg positioning strategy
        for leg_id, controller in self.leg_controllers.items():
            # Move legs to a predefined start position for walking
            default_height = self.config.gait.stance_height
            default_pos = np.array([0.0, default_height])
            
            # Use inverse kinematics to get angles for this position
            angles = controller.kinematics.inverse_kinematics(*default_pos)
            
            if angles is not None:
                # Interpolate between current and target angles
                current_angles = controller.state.current_angles
                interpolated_angles = current_angles + (np.array(angles) - current_angles) * progress
                
                controller.state.current_angles = interpolated_angles
                controller.state.target_angles = np.array(angles)
        
        return False

    def _handle_instability(self):
        self.mode = RobotMode.ERROR
        self.velocity = np.zeros(3)
        self.yaw_rate = 0.0
        for controller in self.leg_controllers.values():
            controller.reset(self.body_height)

    def start_walking(self, velocity: np.ndarray, yaw_rate: float):
        if self.mode == RobotMode.STANDING:
            self.target_velocity = velocity
            self.target_yaw_rate = yaw_rate
            self.mode = RobotMode.TRANSITIONING
            self.transition_start_time = time.time()
            
    def stop_walking(self):
        self.target_velocity = np.zeros(3)
        self.target_yaw_rate = 0.0
        if self.mode != RobotMode.STANDING:
            self.mode = RobotMode.STANDING
            self._reset_leg_positions()
            
    def set_body_height(self, height: float):
        self.target_height = np.clip(
            height,
            self.config.gait.stance_height - 50.0,
            self.config.gait.stance_height + 50.0
        )
            
    def set_gait(self, gait_type: GaitType):
        if self.mode == RobotMode.STANDING:
            self.gait_type = gait_type
            
    def _compute_body_velocity(self) -> np.ndarray:
        speed = np.linalg.norm(self.velocity[:2])
        if speed > self.config.gait.max_velocity:
            scale = self.config.gait.max_velocity / speed
            return self.velocity * scale
        return self.velocity
        
    def _compute_leg_velocity(self, leg_id: LegID, body_vel: np.ndarray) -> np.ndarray:
        offset = self.config.get_leg_offset(leg_id)
        yaw = self.yaw_rate * self.config.dt
        
        R = np.array([
            [np.cos(yaw), -np.sin(yaw), 0],
            [np.sin(yaw), np.cos(yaw), 0],
            [0, 0, 1]
        ])
        
        leg_vel = body_vel + np.cross([0, 0, self.yaw_rate], offset)
        return np.dot(R, leg_vel)
        
    def _reset_leg_positions(self):
        for controller in self.leg_controllers.values():
            controller.reset(self.body_height)
            
    def get_leg_states(self) -> Dict[LegID, Dict[str, float]]:
        states = {}
        for leg_id, controller in self.leg_controllers.items():
            state = controller.get_state()
            states[leg_id] = {
                'angles': state.current_angles.tolist(),
                'torques': state.current_torque.tolist(),
                'contact': state.in_contact
            }
        return states
        
    def get_body_state(self) -> Dict[str, float]:
        return {
            'height': self.body_height,
            'velocity': self.velocity.tolist(),
            'yaw_rate': self.yaw_rate,
            'phase': self.phase,
            'mode': self.mode.name
        }