# Quadruped Kinematics Guide

## Overview
This guide explains the kinematics behind the quadruped movement system. It covers:
- Forward and inverse kinematics
- Step trajectory generation
- Movement strategy
- Gait patterns and stability considerations
- Implementation details and real-world optimizations

---

## 1. Quadruped Leg Kinematics
Each leg of the quadruped has **two degrees of freedom (DOF)**:
- **Hip Joint (θ1):** Controls the forward and backward motion.
- **Knee Joint (θ2):** Controls the height and extension of the foot.

### **Forward Kinematics**
To compute the foot position `(x, y)` given joint angles `(θ1, θ2)`, use:

\[ x = L_1 \cos(\theta_1) + L_2 \cos(\theta_1 + \theta_2) \]
\[ y = L_1 \sin(\theta_1) + L_2 \sin(\theta_1 + \theta_2) \]

Where:
- \( L_1 \) = Upper leg length (0.06m)
- \( L_2 \) = Lower leg length (0.04m)

These equations allow calculating **where the foot is** relative to the quadruped body.

### **Inverse Kinematics**
To determine joint angles `(θ1, θ2)` for a given foot position `(x, y)`, solve:

\[ D = \frac{x^2 + y^2 - L_1^2 - L_2^2}{2 L_1 L_2} \]
\[ \theta_2 = \cos^{-1}(D) \]
\[ \theta_1 = \tan^{-1}(\frac{y}{x}) - \tan^{-1}(\frac{L_2 \sin(\theta_2)}{L_1 + L_2 \cos(\theta_2)}) \]

If \(|D| > 1\), the target position is **out of reach**, and adjustments need to be made.

---

## 2. Step Trajectory Generation
The quadruped follows a predefined trajectory for each step:
- **Step Length:** 0.1m (horizontal movement per step)
- **Step Height:** 0.02m (vertical lift per step)

A sinusoidal trajectory is used for smooth stepping:

\[ y = h \sin(\pi \frac{x + step\_length/2}{step\_length}) \]

Where:
- \( h \) = step height
- \( x \) = position along the step length

This ensures that the foot follows a **natural curve** rather than a sharp linear movement, reducing instability.

---

## 3. Quadruped Movement Strategy
To move forward a total distance \( d \):
1. Compute the number of steps:  
   \[ num\_steps = \frac{d}{step\_length} \]
2. Generate the step trajectory for each leg.
3. Execute movements in a synchronized manner for **stability**.

### **Gait Planning**
A common gait strategy is **trotting** (diagonal legs move together):
- Step **FL + RR** → Step **FR + RL** → Repeat

Other gait options include:
- **Crawling gait:** One leg moves at a time, providing maximum stability.
- **Bounding gait:** Front and rear legs move together in pairs for speed.

The choice of gait affects **stability, speed, and energy efficiency**.

---

## 4. Stability Considerations
Quadruped robots require **proper balance and control** to ensure smooth movement. Key factors include:
- **Center of Mass (CoM):** Must remain within the support polygon for static stability.
- **Zero Moment Point (ZMP):** Used in dynamic walking to predict foot placements.
- **Force Distribution:** Ensuring legs apply even pressure on the ground.
- **Sensor Feedback:** Using IMUs and force sensors to adjust foot positions.

---

## 5. Real-World Implementation
### **Motor Control**
For real-world execution, each joint is controlled by **servo motors**, which need:
- **Precise PWM control** for smooth transitions.
- **Torque calculations** to prevent excessive strain.
- **PID controllers** to maintain accuracy.

### **Environmental Adaptation**
Quadrupeds may need to adapt to different terrains:
- **Flat surfaces:** Standard gait works efficiently.
- **Uneven terrain:** Requires **sensor feedback** for dynamic adjustments.
- **Slopes:** Adjusts step height and angle for proper footing.

---

## 6. Example Implementation
```python
quadruped = QuadrupedMovementSolver()
total_distance = 0.2  # Move forward 0.2 meters
movement_plan = quadruped.move_forward(total_distance)
```
This function generates step sequences for **all four legs**, ensuring a stable gait.

---

## 7. Optimizing Quadruped Motion
- **Adjust step length:** Shorter steps improve control, longer steps increase speed.
- **Fine-tune step height:** Lower heights save energy, but higher steps avoid obstacles.
- **Add terrain sensing:** Using LiDAR or IMUs for real-time adaptation.
- **Energy-efficient gaits:** Minimize unnecessary joint movements.

---

## Conclusion
This guide provides the foundation for quadruped motion planning. Adjustments to **step length, step height, gait strategy, and terrain adaptation** can optimize performance for different environments.

For real-world implementation, consider integrating **IMU feedback, PID motor control, and terrain-aware walking strategies** for advanced capabilities.

