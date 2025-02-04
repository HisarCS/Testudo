import numpy as np
from typing import Dict, List
from config import RobotConfig, LegID
from leg_controller import LegState

class StabilityController:
    def __init__(self, config: RobotConfig):
        self.config = config
        self.com_position = np.zeros(3)
        self.com_velocity = np.zeros(3)
        
    def update(self, leg_states: Dict[LegID, Dict]) -> bool:
        contact_points = []
        total_force = np.zeros(3)
        
        for leg_id, state in leg_states.items():
            if state['contact']:  # Corrected line
                foot_pos = self.config.get_leg_offset(leg_id)
                contact_points.append(foot_pos[:2])
                
                world_force = np.array([
                    state['foot_force'][0],  # Corrected line
                    0,
                    state['foot_force'][1]   # Corrected line
                ])
                total_force += world_force
                
        if len(contact_points) < 2:
            return False
            
        self._update_com_dynamics(total_force)
        return self._check_stability(contact_points)
        
    def _update_com_dynamics(self, total_force: np.ndarray):
        dt = self.config.dt
        mass = self.config.body_mass
        gravity = np.array([0, 0, -self.config.gravity])
        
        acceleration = total_force / mass + gravity
        self.com_velocity += acceleration * dt
        self.com_position += self.com_velocity * dt
        
    def _check_stability(self, contact_points: List[np.ndarray]) -> bool:
        if len(contact_points) < 3:
            return False
            
        com_xy = self.com_position[:2]
        hull = self._compute_convex_hull(contact_points)
        
        if not hull:
            return False
            
        return self._point_in_polygon(com_xy, hull)
        
    def _compute_convex_hull(self, points: List[np.ndarray]) -> List[np.ndarray]:
        if len(points) < 3:
            return []
            
        def cross_product_2d(o: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
            
        points = sorted(points, key=lambda p: (p[0], p[1]))
        lower = []
        
        for p in points:
            while len(lower) >= 2 and cross_product_2d(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
            
        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and cross_product_2d(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
            
        return lower[:-1] + upper[:-1]
        
    def _point_in_polygon(self, point: np.ndarray, polygon: List[np.ndarray]) -> bool:
        if not polygon:
            return False
            
        n = len(polygon)
        inside = False
        
        j = n - 1
        for i in range(n):
            if (((polygon[i][1] > point[1]) != (polygon[j][1] > point[1])) and
                (point[0] < (polygon[j][0] - polygon[i][0]) * 
                 (point[1] - polygon[i][1]) / 
                 (polygon[j][1] - polygon[i][1]) + polygon[i][0])):
                inside = not inside
            j = i
            
        margin = self.config.gait.stability_margin
        if inside:
            min_dist = float('inf')
            for i in range(n):
                j = (i + 1) % n
                edge = polygon[j] - polygon[i]
                normal = np.array([-edge[1], edge[0]])
                normal /= np.linalg.norm(normal)
                
                dist = abs(np.dot(point - polygon[i], normal))
                min_dist = min(min_dist, dist)
                
            return min_dist >= margin
            
        return False