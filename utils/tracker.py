# fitness_tracker/utils/tracker.py
import numpy as np

# COCO Keypoint indices (for reference, match YOLOv8 output)
# 0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
# 5: left_shoulder, 6: right_shoulder, 7: left_elbow, 8: right_elbow
# 9: left_wrist, 10: right_wrist, 11: left_hip, 12: right_hip
# 13: left_knee, 14: right_knee, 15: left_ankle, 16: right_ankle

def calculate_angle(a, b, c):
    """Calculates the angle between three points (a, b, c) with b as the vertex."""
    a = np.array(a)  # First point
    b = np.array(b)  # Mid point (vertex)
    c = np.array(c)  # End point

    # Check if any point is [0,0] (often indicates not detected clearly or out of frame)
    if np.array_equal(a, [0,0]) or np.array_equal(b, [0,0]) or np.array_equal(c, [0,0]):
        return None 

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
              np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle
    return angle

if __name__ == '__main__':
    shoulder = [100, 100]
    elbow = [150, 150]
    wrist = [100, 200]
    angle = calculate_angle(shoulder, elbow, wrist)
    print(f"Calculated angle: {angle} degrees")

    hip = [200, 300]
    knee = [200, 400]
    ankle = [200, 500]
    angle_straight = calculate_angle(hip, knee, ankle)
    print(f"Calculated straight angle: {angle_straight} degrees")