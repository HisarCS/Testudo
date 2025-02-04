import numpy as np
from typing import Dict, List, Tuple, Optional
from core import (
    physical_params, gait_params, RobotState, 
    GaitType, GAIT_PHASE_OFFSETS, LEG_LABELS,
    get_default_stance
)

class GaitGenerator:
    def __init__(self, gait_type: GaitType = GaitType.TROT):
        self.gait_type = gait_type
        self.phase_offsets = GAIT_PHASE_OFFSETS[gait_type]
        self.stance = get_default_stance()
        self.swing_height = gait_params.STEP_HEIGHT
        self.step_length = gait_params.STEP_LENGTH
        
    def get_foot_trajectory(self, phase: float, leg_id: str) -> np.ndarray:
        """
        Get foot position for given phase and leg
        phase: [0, 1] representing full gait cycle
        """
        # Adjust phase based on leg's offset
        adj_phase = (phase + self.phase_offsets[leg_id]) % 1.0
        
        # Determine if in swing or stance
        if adj_phase < gait_params.DUTY_FACTOR:
            return self._stance_trajectory(adj_phase, leg_id)
        else:
            return self._swing_trajectory(adj_phase, leg_id)
    
    def _stance_trajectory(self, phase: float, leg_id: str) -> np.ndarray:
        """Generate stance phase trajectory"""
        # Normalize phase to [0, 1] for stance duration
        norm_phase = phase / gait_params.DUTY_FACTOR
        
        # Linear motion backwards relative to body
        start_pos = self.stance[leg_id] + np.array([self.step_length/2, 0, 0])
        end_pos = self.stance[leg_id] + np.array([-self.step_length/2, 0, 0])
        
        return start_pos + norm_phase * (end_pos - start_pos)
    
    def _swing_trajectory(self, phase: float, leg_id: str) -> np.ndarray:
        """Generate swing phase trajectory"""
        # Normalize phase to [0, 1] for swing duration
        swing_phase = (phase - gait_params.DUTY_FACTOR) / (1 - gait_params.DUTY_FACTOR)
        
        # Start and end positions
        start_pos = self.stance[leg_id] + np.array([-self.step_length/2, 0, 0])
        end_pos = self.stance[leg_id] + np.array([self.step_length/2, 0, 0])
        
        # Add vertical component for foot clearance
        x = start_pos[0] + swing_phase * (end_pos[0] - start_pos[0])
        y = start_pos[1] + swing_phase * (end_pos[1] - start_pos[1])
        z = start_pos[2] + self.swing_height * np.sin(np.pi * swing_phase)
        
        return np.array([x, y, z])
    
    def get_stance_legs(self, phase: float) -> List[str]:
        """Return list of legs currently in stance phase"""
        stance_legs = []
        for leg_id in LEG_LABELS:
            adj_phase = (phase + self.phase_offsets[leg_id]) % 1.0
            if adj_phase < gait_params.DUTY_FACTOR:
                stance_legs.append(leg_id)
        return stance_legs
    
    def get_next_foot_positions(self, phase: float) -> Dict[str, np.ndarray]:
        """Get all foot positions for current phase"""
        return {
            leg_id: self.get_foot_trajectory(phase, leg_id)
            for leg_id in LEG_LABELS
        }

def generate_swing_trajectory(
    start: np.ndarray, 
    end: np.ndarray, 
    steps: int
) -> List[np.ndarray]:
    """Generate array of positions for swing phase"""
    trajectory = []
    for i in range(steps):
        phase = i / (steps - 1)
        x = start[0] + phase * (end[0] - start[0])
        y = start[1] + phase * (end[1] - start[1])
        z = start[2] + gait_params.STEP_HEIGHT * np.sin(np.pi * phase)
        trajectory.append(np.array([x, y, z]))
    return trajectory