import numpy as np

class QuadrupedMovementSolver:
    def __init__(
        self,
        L1=0.06,              # Upper leg length (meters)
        L2=0.04,              # Lower leg length (meters)
        body_length=0.20,     # Length of body (meters)
        body_width=0.10,      # Width of body (meters)
        step_length=0.10,     # Forward distance covered in each step
        step_height=0.02,     # Foot lift (peak) for each step
        step_count=10,        # Number of discretized points per single step
        gait_type='trot',     # Type of gait; here we'll implement a simple trot example
        com_x_offset=0.0,     # COM offset in the robot body frame (if needed)
        com_y_offset=0.0,
        com_z_offset=0.0
    ):
        """
        A more realistic 3D quadruped solver with:
          - Leg offsets in 3D
          - Basic gait phasing (trot)
          - Partial step handling
          - Simple stability check
        """
        self.L1 = L1
        self.L2 = L2
        self.body_length = body_length
        self.body_width = body_width

        self.step_length = step_length
        self.step_height = step_height
        self.step_count = step_count
        self.gait_type = gait_type

        # Approximate center of mass in the body frame
        self.com_offset = np.array([com_x_offset, com_y_offset, com_z_offset])

        # Define leg labels
        # Front-Left, Front-Right, Rear-Left, Rear-Right
        self.legs = ['FL', 'FR', 'RL', 'RR']

        # Each leg’s "hip" origin in the robot body frame (x forward, y left, z up)
        # Here, we assume the body is centered at (0,0,0), and legs attach near the corners.
        half_length = body_length / 2.0
        half_width  = body_width  / 2.0

        self.leg_origins = {
            'FL': np.array([+half_length, +half_width, 0.0]),  # Front-Left
            'FR': np.array([+half_length, -half_width, 0.0]),  # Front-Right
            'RL': np.array([-half_length, +half_width, 0.0]),  # Rear-Left
            'RR': np.array([-half_length, -half_width, 0.0])   # Rear-Right
        }

        # Gait phase offsets in [0, 1) for each leg in one stride
        # Simple trot: FL & RR move together; FR & RL move together
        # e.g., FL & RR have phase offset 0.0, FR & RL have offset 0.5
        if self.gait_type == 'trot':
            self.leg_phases = {
                'FL': 0.00,
                'RR': 0.00,
                'FR': 0.50,
                'RL': 0.50
            }
        else:
            # You could add other gaits (walk, bound, etc.)
            # For now, default to trot if unspecified
            self.leg_phases = {
                'FL': 0.00,
                'RR': 0.00,
                'FR': 0.50,
                'RL': 0.50
            }

    def transform_to_leg_frame(self, foot_pos_body, leg_label):
        """
        Transform foot position from the *body frame* to the *local leg frame*.
        For this simple demo:
          - We assume no body rotation (pitch/roll/yaw = 0).
          - We only offset by the leg's origin.

        :param foot_pos_body: (x, y, z) in the body frame.
        :param leg_label: which leg we're transforming for.
        :return: (x_leg, y_leg, z_leg) in the leg's local coordinate system.
        """
        hip_origin = self.leg_origins[leg_label]
        # Leg frame: the hip joint is at (0,0,0) in that leg's local frame
        return foot_pos_body - hip_origin

    def inverse_kinematics_2link(self, x, y, z):
        """
        Simple 2-link IK in a vertical plane (pitch-only).
        We assume the leg is in the plane spanned by, say, z down and x forward.
        'y' is ignored in the sense we do not have abduction/adduction in this simplified model.

        So effectively:
           1) Project (x, y, z) onto the plane spanned by (x, z).
           2) Let R = sqrt(x^2 + z^2) (distance in that plane).
           3) Solve 2-link planar IK for R, ignoring y offset.

        If you want a 3-joint solution (hip yaw, hip pitch, knee pitch), that is more involved,
        but below is a minimal demonstration.

        :return: (theta_hip, theta_knee) in radians, or (None, None) if unreachable.
        """
        R = np.sqrt(x**2 + z**2)
        # 2-link planar approach:
        # D = (R^2 - L1^2 - L2^2) / (2 * L1 * L2)
        D = (R**2 - self.L1**2 - self.L2**2) / (2.0 * self.L1 * self.L2)
        if abs(D) > 1.0:
            return None, None  # unreachable

        theta_knee = np.arccos(D)

        # For the hip angle, define alpha = atan2(z, x)
        # Then solve for the angle that meets the 2-link geometry
        alpha = np.arctan2(z, x)
        # Beta = atan2(L2 sin(knee), L1 + L2 cos(knee))
        beta = np.arctan2(self.L2 * np.sin(theta_knee),
                          self.L1 + self.L2 * np.cos(theta_knee))

        theta_hip = alpha - beta

        return theta_hip, theta_knee

    def generate_swing_trajectory(self, start_pos, end_pos, leg_label, phase, steps):
        """
        Generate a 3D foot trajectory (swing phase) for one leg from start_pos to end_pos
        in the BODY frame. We'll lift the foot by `self.step_height` at the midpoint.

        We'll use a simple trapezoid or sine shape in the vertical dimension (z).
        This function returns a list of foot positions in the body frame.

        :param start_pos: (x, y, z) foot start in body frame
        :param end_pos:   (x, y, z) foot end in body frame
        :param leg_label: leg ID
        :param phase:     normalized phase offset [0..1) for the gait
        :param steps:     number of points in the swing
        :return: list of (x_body, y_body, z_body) points
        """
        trajectory = []
        # Create a linear interpolation from start to end in x,y
        x_vals = np.linspace(start_pos[0], end_pos[0], steps)
        y_vals = np.linspace(start_pos[1], end_pos[1], steps)

        # For the z dimension, make a simple half-sine "lift"
        # Start and end at ground level (start_pos[2], end_pos[2]).
        # We assume both are about the same ground contact (z).
        z_start = start_pos[2]
        z_end   = end_pos[2]

        # We'll blend from z_start up to z_start+step_height at midpoint, then down to z_end
        # with a sine wave for smoothness.
        z_vals = []
        for i in range(steps):
            t = i / (steps - 1)  # goes from 0 to 1
            lift = self.step_height * np.sin(np.pi * t)
            # Interpolate base z from z_start to z_end
            z_lin = z_start + (z_end - z_start) * t
            z_vals.append(z_lin + lift)

        for i in range(steps):
            trajectory.append(np.array([x_vals[i], y_vals[i], z_vals[i]]))

        return trajectory

    def generate_stance_trajectory(self, start_pos, end_pos, steps):
        """
        Generate foot positions during the stance phase (on the ground). Typically,
        the foot is stationary or moving slightly with the body. For simplicity,
        we can linearly interpolate at ground level from start to end.
        """
        trajectory = []
        x_vals = np.linspace(start_pos[0], end_pos[0], steps)
        y_vals = np.linspace(start_pos[1], end_pos[1], steps)
        z_vals = np.linspace(start_pos[2], end_pos[2], steps)  # should be near ground contact

        for i in range(steps):
            trajectory.append(np.array([x_vals[i], y_vals[i], z_vals[i]]))

        return trajectory

    def check_stability(self, foot_positions):
        """
        Very rough stability check:
          - Project foot positions onto the ground plane (x,y).
          - Compute center of mass projection (x_com, y_com).
          - Check if (x_com, y_com) is inside the convex hull of the stance foot positions.

        :param foot_positions: dict(leg_label -> (x,y,z) in body frame) 
                               for the legs that are in stance.
        :return: Boolean, True if stable.
        """
        # Collect stance points (x,y)
        stance_points = np.array([[pos[0], pos[1]] for pos in foot_positions.values()])
        # Project COM (assuming it's at self.com_offset in the body frame)
        com_xy = self.com_offset[:2]

        if len(stance_points) < 3:
            # Not enough points for a polygon. Return False or True by definition.
            return False

        # Convex hull or polygon test. For brevity, do a simple "ray casting" or "winding" check.
        # We'll implement a minimal polygon containment check:
        return self.point_in_polygon_2d(com_xy, stance_points)

    def point_in_polygon_2d(self, point, polygon):
        """
        Ray-casting or winding number approach. 
        Minimal implementation for demonstration.
        :param point: (x, y)
        :param polygon: Nx2 array of vertices
        :return: True if the point is inside the polygon
        """
        x, y = point
        inside = False
        n = len(polygon)
        for i in range(n):
            x_i, y_i = polygon[i]
            x_j, y_j = polygon[(i+1) % n]
            # Check edges
            intersect = ((y_i > y) != (y_j > y)) and \
                        (x < (x_j - x_i) * (y - y_i) / (y_j - y_i) + x_i)
            if intersect:
                inside = not inside
        return inside

    def move_forward(self, distance, ground_z=-0.02):
        """
        Orchestrate the gait cycle to move the robot forward by 'distance'.

        For each full stride:
          - half the time, FL & RR in swing, FR & RL in stance (trot)
          - second half, FR & RL in swing, FL & RR in stance
        We also handle partial final steps if distance is not a multiple of step_length.

        :param distance: total forward distance in meters
        :param ground_z: approximate ground contact level (negative if robot origin is above ground)
        :return: A list (timeline) of dictionary describing each leg's foot position in body frame
                 and corresponding joint angles.
        """
        # Number of full steps (strides) for the given distance
        num_full_strides = int(distance // self.step_length)
        remainder = distance - num_full_strides * self.step_length

        # We'll accumulate a "global" forward offset that increments after each stride
        current_x_offset = 0.0

        # Store final timeline of foot states
        # timeline: list of [ {leg_label: (pos, (theta_hip, theta_knee)), ...}, ... ]
        timeline = []

        # Helper to get stance or swing points
        def foot_trajectory(leg, start_pos_body, end_pos_body, is_swing):
            # Decide how many points for stance vs swing
            # We'll do half the time in swing, half in stance for trot, but that’s a bit simplified.
            # For demonstration, just split self.step_count in half:
            steps_swing = self.step_count
            steps_stance = self.step_count

            if is_swing:
                return self.generate_swing_trajectory(start_pos_body, end_pos_body, leg,
                                                      self.leg_phases[leg], steps_swing)
            else:
                return self.generate_stance_trajectory(start_pos_body, end_pos_body, steps_stance)

        # Initialize each foot at the ground at x=leg_origin.x (body frame), z=ground_z
        # We'll say the robot is standing with feet directly under the hip (no offset in x).
        foot_positions_body = {}
        for leg in self.legs:
            origin = self.leg_origins[leg]
            foot_positions_body[leg] = np.array([origin[0], origin[1], ground_z])

        def record_timeline(leg_paths):
            """
            leg_paths: dict(leg -> list of 3D positions).
            We iterate over all the 'steps' simultaneously, building frames of data.
            """
            max_len = max(len(path) for path in leg_paths.values())
            for i in range(max_len):
                frame_data = {}
                for leg, path in leg_paths.items():
                    idx = min(i, len(path)-1)  # clamp
                    pos_body = path[idx]
                    # Compute IK in the leg frame
                    pos_leg = self.transform_to_leg_frame(pos_body, leg)
                    theta_hip, theta_knee = self.inverse_kinematics_2link(
                        pos_leg[0], pos_leg[1], pos_leg[2]
                    )
                    frame_data[leg] = (pos_body, (theta_hip, theta_knee))
                # You could do a stability check here if you want to skip or adjust frames
                timeline.append(frame_data)

        # Construct gait cycles
        strides_needed = num_full_strides + (1 if remainder > 1e-6 else 0)
        for s in range(strides_needed):
            # This stride length
            stride_len = self.step_length if (s < num_full_strides) else remainder
            if stride_len < 1e-6:
                break

            # We'll define that half the cycle is FL & RR swinging, half is FR & RL swinging
            # For trot, we do 2 phases per stride.

            # --------------------
            # Phase A: FL & RR swing, FR & RL stance
            leg_paths_A = {}
            for leg in self.legs:
                start_pos = foot_positions_body[leg].copy()
                # End pos is the same if stance, or advanced in x if swing
                if leg in ['FL','RR']:
                    # Swing: foot moves forward by stride_len
                    end_pos = start_pos + np.array([stride_len, 0, 0])
                    # Keep foot on ground at start, lifts in trajectory
                    path = foot_trajectory(leg, start_pos, end_pos, is_swing=True)
                else:
                    # Stance: maybe foot remains near the same x if we imagine the body moving
                    # but for demonstration, let's shift backward by stride_len so body moves forward.
                    # This is inverted perspective: the foot "appears" stationary in world,
                    # but in the body frame it shifts backward.
                    end_pos = start_pos - np.array([stride_len, 0, 0])
                    path = foot_trajectory(leg, start_pos, end_pos, is_swing=False)

                leg_paths_A[leg] = path

            # Update timeline
            record_timeline(leg_paths_A)
            # Update foot positions to final
            for leg in self.legs:
                foot_positions_body[leg] = leg_paths_A[leg][-1]

            # --------------------
            # Phase B: FR & RL swing, FL & RR stance
            leg_paths_B = {}
            for leg in self.legs:
                start_pos = foot_positions_body[leg].copy()
                if leg in ['FR','RL']:
                    # Swing
                    end_pos = start_pos + np.array([stride_len, 0, 0])
                    path = foot_trajectory(leg, start_pos, end_pos, is_swing=True)
                else:
                    # Stance
                    end_pos = start_pos - np.array([stride_len, 0, 0])
                    path = foot_trajectory(leg, start_pos, end_pos, is_swing=False)

                leg_paths_B[leg] = path

            record_timeline(leg_paths_B)
            # Update foot positions
            for leg in self.legs:
                foot_positions_body[leg] = leg_paths_B[leg][-1]

            # After completing both phases, we consider that the body has moved forward by stride_len * 2 phases
            current_x_offset += stride_len

        return timeline


if __name__ == "__main__":
    # -------------------------
    # EXAMPLE USAGE
    # -------------------------
    quadruped = QuadrupedMovementSolver(
        L1=0.10,
        L2=0.10,
        body_length=0.30,
        body_width=0.15,
        step_length=0.15,
        step_height=0.03,
        step_count=10,
        gait_type='trot'
    )

    total_distance = 0.45 
    motion_plan = quadruped.move_forward(distance=total_distance, ground_z=-0.05)


    print(f"Generated motion plan with {len(motion_plan)} frames for distance {total_distance:.2f} m.")
    for i, frame in enumerate(motion_plan[:5]):  
        print(f"\nFrame {i+1}:")
        for leg, (pos_body, angles) in frame.items():
            (theta_hip, theta_knee) = angles
            if theta_hip is None or theta_knee is None:
                print(f"  {leg}: pos={pos_body}, IK=Out of reach")
            else:
                print(f"  {leg}: pos={pos_body}, hip={theta_hip:.3f}, knee={theta_knee:.3f}")
