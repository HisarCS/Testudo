import numpy as np
from typing import Tuple, Optional
from config import RobotConfig, LegID, RobotMode
from kinematics import LegKinematics
import time

class LegState:
    def __init__(self, config: RobotConfig):
        self.current_angles = np.zeros(2)
        self.target_angles = np.zeros(2)
        self.current_velocity = np.zeros(2)
        self.target_velocity = np.zeros(2)
        self.current_torque = np.zeros(2)
        self.foot_force = np.zeros(2)
        self.in_contact = False
        self.contact_time = 0.0
        self.last_ground_x = 0.0
        self.stance_depth = config.gait.stance_height
        self.step_height = config.gait.step_height
        self.phase = 0.0
        self.touchdown_phase = 0.0
        self.liftoff_phase = 0.0
        self.in_stance = True
        self.was_in_stance = True

class Trajectory:
    def __init__(self):
        self.start_pos = np.zeros(2)
        self.end_pos = np.zeros(2)
        self.start_time = 0.0
        self.duration = 1.0  # Initialize with a non-zero value
        self.height = 0.0
        
    def get_point(self, t: float) -> np.ndarray:
        if self.duration <= 0.0:
            return self.start_pos  # Return the start position if duration is zero or negative
        phase = np.clip((t - self.start_time) / self.duration, 0.0, 1.0)
        x = self.start_pos[0] + phase * (self.end_pos[0] - self.start_pos[0])
        y = self.start_pos[1] + phase * (self.end_pos[1] - self.start_pos[1])
        z_lift = self.height * np.sin(np.pi * phase)
        return np.array([x, y + z_lift])

class LegController:
    def __init__(self, leg_id: LegID, config: RobotConfig):
        self.leg_id = leg_id
        self.config = config
        self.kinematics = LegKinematics(config.leg)
        self.state = LegState(config)
        self.trajectory = Trajectory()
        self.last_time = time.time()
        
    def update(self, phase: float, velocity: np.ndarray):
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        self._update_gait_phase(phase)
        self._update_trajectory(velocity)
        self._update_leg_state(dt)
        self._apply_joint_control(dt)
        
    def _update_gait_phase(self, phase: float):
        self.state.phase = phase
        gait_offset = self.config.gait.phase_offset[self.leg_id]
        adjusted_phase = (phase + gait_offset) % 1.0
        
        if adjusted_phase < self.config.gait.duty_factor:
            if not self.state.in_stance:
                self.state.touchdown_phase = adjusted_phase
                self.state.in_stance = True
        else:
            if self.state.in_stance:
                self.state.liftoff_phase = adjusted_phase
                self.state.in_stance = False
                
        self.state.was_in_stance = self.state.in_stance
        
    def _update_trajectory(self, velocity: np.ndarray):
        if self.state.in_stance != self.state.was_in_stance:
            current_pos = self.kinematics.forward_kinematics(*self.state.current_angles)
            
            if self.state.in_stance:
                self.trajectory.start_pos = current_pos
                step_time = max(self.config.gait.stance_time, 1e-6)  # Ensure non-zero duration
                step_length = velocity[0] * step_time
                self.trajectory.end_pos = np.array([
                    current_pos[0] + step_length,
                    self.state.stance_depth
                ])
                self.trajectory.height = 0.0
            else:
                self.trajectory.start_pos = current_pos
                swing_time = max(self.config.gait.swing_time, 1e-6)  # Ensure non-zero duration
                step_length = velocity[0] * swing_time
                self.trajectory.end_pos = np.array([
                    current_pos[0] + step_length,
                    self.state.stance_depth
                ])
                self.trajectory.height = self.state.step_height
            
            self.trajectory.start_time = time.time()
            self.trajectory.duration = step_time if self.state.in_stance else swing_time
            
    def _update_leg_state(self, dt: float):
        t = time.time()
        target_pos = self.trajectory.get_point(t)
        
        angles = self.kinematics.inverse_kinematics(target_pos[0], target_pos[1])
        if angles is not None:
            self.state.target_angles = np.array(angles)
            
            J = self.kinematics.compute_jacobian(*angles)
            if dt > 0:
                target_vel = (target_pos - self.trajectory.get_point(t - dt)) / dt
                self.state.target_velocity = np.linalg.lstsq(J, target_vel, rcond=None)[0]
            else:
                self.state.target_velocity = np.zeros(2)
            
            if self.state.in_stance:
                ground_force = self._compute_ground_force()
                self.state.current_torque = self.kinematics.compute_torques(
                    *angles, *ground_force)
            else:
                self.state.current_torque = np.zeros(2)
                
    def _apply_joint_control(self, dt: float):
        kp = np.array([100.0, 100.0])
        kd = np.array([1.0, 1.0])
        
        angle_error = self.state.target_angles - self.state.current_angles
        velocity_error = self.state.target_velocity - self.state.current_velocity
        
        torque_feedback = kp * angle_error + kd * velocity_error
        total_torque = self.state.current_torque + torque_feedback
        
        torque_limits = np.array([
            self.config.leg.servo_upper.max_torque,
            self.config.leg.servo_lower.max_torque
        ])
        
        self.state.current_torque = np.clip(total_torque, -torque_limits, torque_limits)
        
        max_velocity = np.array([
            self.config.leg.servo_upper.max_speed,
            self.config.leg.servo_lower.max_speed
        ]) * 60.0  # Convert to deg/s
        
        angle_change = self.state.current_velocity * dt
        angle_change = np.clip(angle_change, -max_velocity * dt, max_velocity * dt)
        self.state.current_angles += angle_change
        
    def _compute_ground_force(self) -> np.ndarray:
        k_ground = 1000.0
        b_ground = 10.0
        
        foot_pos = self.kinematics.forward_kinematics(*self.state.current_angles)
        penetration = max(0, -foot_pos[1])
        
        if penetration > 0:
            self.state.in_contact = True
            self.state.contact_time += self.config.dt
        else:
            self.state.in_contact = False
            self.state.contact_time = 0
            
        if self.state.in_contact:
            normal_force = k_ground * penetration
            dx = foot_pos[0] - self.state.last_ground_x
            friction_force = -self.config.leg.foot_friction * normal_force * np.sign(dx)
            
            self.state.foot_force = np.array([friction_force, normal_force])
            self.state.last_ground_x = foot_pos[0]
        else:
            self.state.foot_force = np.zeros(2)
            
        return self.state.foot_force
            
    def get_state(self) -> LegState:
        return self.state
        
    def reset(self, height: float):
        self.state = LegState(self.config)
        self.state.stance_depth = height
        target_pos = np.array([0, height])
        angles = self.kinematics.inverse_kinematics(*target_pos)
        if angles is not None:
            self.state.current_angles = np.array(angles)
            self.state.target_angles = np.array(angles)