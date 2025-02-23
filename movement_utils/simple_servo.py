from adafruit_servokit import ServoKit

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

set_servo_angle(0, 180)