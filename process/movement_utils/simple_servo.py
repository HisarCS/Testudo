from adafruit_servokit import ServoKit
import time

# Create a ServoKit instance for a 16-channel servo driver
kit = ServoKit(channels=16)

def set_servo_angle(channel, angle):
    """
    Sets the servo on the specified channel to the given angle (in degrees).

    :param channel: The servo channel (0-15) on the PCA9685 board.
    :param angle:   The desired servo angle. Typically ranges between 0 and 180.
    """
    # Optional: Clamp the angle to valid servo range
    angle = max(0, min(angle, 180))  # ensures angle is between 0 and 180

    kit.servo[channel].angle = angle
    print(f"Servo on channel {channel} set to {angle}°")

def move_back():
    for i in range(0, 10):
        set_servo_angle(3, 55)
        set_servo_angle(6, 0)
        set_servo_angle(12, 125)
        set_servo_angle(15, 140)
        time.sleep(1)
        set_servo_angle(3, 140)
        set_servo_angle(6, 95)
        set_servo_angle(12, 40)
        set_servo_angle(15, 40)
        time.sleep(1)

def move_forward():
    for i in range(10):
        # First position for moving forward (using the second position from move_back)
        set_servo_angle(3, 140)
        set_servo_angle(6, 95)
        set_servo_angle(12, 40)
        set_servo_angle(15, 40)
        time.sleep(1)
        # Second position for moving forward (using the first position from move_back)
        set_servo_angle(3, 55)
        set_servo_angle(6, 0)
        set_servo_angle(12, 125)
        set_servo_angle(15, 140)
        time.sleep(1)