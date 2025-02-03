# Quadruped Kinematics Guide

## Introduction
This guide provides an overview of the kinematic model used in a quadruped robot simulation. The model includes:
- **Inverse kinematics (IK) for leg control**
- **Forward movement generation**
- **Gait phasing and trajectory planning**

The model assumes a **2-link robotic leg structure** with **hip and knee joints**, along with a **trot gait** for movement.

---

## Leg Structure and Coordinate System
Each leg consists of:
- **L1 (Upper leg length):** 6 cm
- **L2 (Lower leg length):** 4 cm

Legs are attached at **four corners of the robot’s body**:
- **Front Left (FL)**
- **Front Right (FR)**
- **Rear Left (RL)**
- **Rear Right (RR)**

The robot's **center of mass (COM)** is at the body center.

---

## Inverse Kinematics (IK)
The inverse kinematics solver calculates the required joint angles (**hip & knee**) to reach a specific foot position in the **leg’s local coordinate frame**.

### Equations:
#### **1. Compute Distance from Hip to Foot**
\[
R = \sqrt{x^2 + z^2}
\]

#### **2. Compute Knee Angle**
\[
\theta_2 = \cos^{-1}\left( \frac{R^2 - L1^2 - L2^2}{2 \cdot L1 \cdot L2} \right)
\]

#### **3. Compute Hip Angle**
\[
\theta_1 = \tan^{-1}\left( \frac{z}{x} \right) - \tan^{-1}\left( \frac{L2 \sin(\theta_2)}{L1 + L2 \cos(\theta_2)} \right)
\]

These angles are used to drive the **servo motors** for precise foot placement.

---

## Step Trajectory Generation
The quadruped follows a **trot gait**, meaning **diagonal pairs of legs move together**. The trajectory follows a **smooth, sinusoidal path**:

### **Step Height & Length**
- **Step Length:** 10 cm
- **Step Height:** 2 cm

Foot motion follows a **half-sine wave** for a **smooth step transition**:
\[
y = h \sin \left( \pi \frac{x + L/2}{L} \right)
\]
where:
- \(h\) = Step height
- \(L\) = Step length

---

## Gait Planning
The quadruped uses **gait phasing** to ensure stable walking. Each leg moves with a phase offset:

### **Trot Gait Phasing**
| Leg  | Phase Offset |
|------|-------------|
| FL   | 0.00        |
| RR   | 0.00        |
| FR   | 0.50        |
| RL   | 0.50        |

This means **FL and RR legs move together**, while **FR and RL legs move together**.

---

## Stability Check
To maintain balance, the quadruped performs a **stability check**:
1. **Projects foot positions onto the ground plane**
2. **Computes the center of mass (COM) projection**
3. **Ensures the COM projection remains inside the stance foot polygon**

This ensures that the quadruped does not tip over while walking.

---

## Moving Forward
The quadruped advances by executing **alternating swing and stance phases**:
1. **Phase A:** FL & RR swing forward, FR & RL remain grounded
2. **Phase B:** FR & RL swing forward, FL & RR remain grounded

Each full cycle **advances the robot by one step length**.

### **Full Motion Execution**
To move forward by `distance D`:
\[
N_{steps} = \frac{D}{L_{step}}
\]
where:
- \(D\) = Target distance
- \(L_{step}\) = Step length

Each step consists of **10 discretized motion points** for smooth movement.

---

## Summary
- **Inverse kinematics** calculates joint angles for each step.
- **Step trajectory** ensures smooth foot placement.
- **Gait phasing** keeps the robot stable.
- **Full motion planning** moves the quadruped forward efficiently.

By implementing this model, we achieve a functional **quadruped walking algorithm**!
