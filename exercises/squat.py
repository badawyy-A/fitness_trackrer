# fitness_tracker/exercises/squat.py
import cv2
import numpy as np
from utils.tracker import calculate_angle

class SquatTracker:
    def __init__(self):
        self.reps = 0
        self.stage = "UP"  # Can be "UP" or "DOWN"
        self.feedback = "Start Squats"
        
        # Thresholds (VERY IMPORTANT - TUNE THESE)
        self.knee_angle_down_threshold = 100 # Max angle for knee when squatted (more bent)
        self.hip_angle_down_threshold = 100  # Max angle for hip when squatted (more bent)
        self.knee_angle_up_threshold = 160   # Min angle for knee when standing (straighter)
        self.hip_angle_up_threshold = 160    # Min angle for hip when standing (straighter)

    def process_frame(self, keypoints_xy, frame):
        if keypoints_xy.shape[0] < 17:
            self.feedback = "Not all keypoints visible"
            return self.reps, self.feedback, frame

        r_hip = keypoints_xy[12]
        r_knee = keypoints_xy[14]
        r_ankle = keypoints_xy[16]
        r_shoulder = keypoints_xy[6] 

        l_hip = keypoints_xy[11]
        l_knee = keypoints_xy[13]
        l_ankle = keypoints_xy[15]
        l_shoulder = keypoints_xy[5]

        right_knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
        right_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee) # Using shoulder-hip-knee for hip bend
        
        left_knee_angle = calculate_angle(l_hip, l_knee, l_ankle)
        left_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee) # Using shoulder-hip-knee

        knee_angle = None
        hip_angle = None
        
        valid_right = right_knee_angle is not None and right_hip_angle is not None
        valid_left = left_knee_angle is not None and left_hip_angle is not None

        display_knee_pt, display_hip_pt = None, None

        if valid_right and valid_left:
            knee_angle = (right_knee_angle + left_knee_angle) / 2
            hip_angle = (right_hip_angle + left_hip_angle) / 2
            display_knee_pt = (int((r_knee[0]+l_knee[0])/2 + 10), int((r_knee[1]+l_knee[1])/2))
            display_hip_pt = (int((r_hip[0]+l_hip[0])/2 + 10), int((r_hip[1]+l_hip[1])/2))
        elif valid_right:
            knee_angle = right_knee_angle
            hip_angle = right_hip_angle
            display_knee_pt = (int(r_knee[0] + 10), int(r_knee[1]))
            display_hip_pt = (int(r_hip[0] + 10), int(r_hip[1]))
        elif valid_left:
            knee_angle = left_knee_angle
            hip_angle = left_hip_angle
            display_knee_pt = (int(l_knee[0] + 10), int(l_knee[1]))
            display_hip_pt = (int(l_hip[0] + 10), int(l_hip[1]))
        
        # --- DEBUG PRINT ---
        # print(f"Squat - Stage: {self.stage}, Knee: {knee_angle}, Hip: {hip_angle}, Reps: {self.reps}")
        # --- END DEBUG ---

        if knee_angle is None or hip_angle is None or display_knee_pt is None or display_hip_pt is None:
            self.feedback = "Ensure legs and hips are clearly visible."
            return self.reps, self.feedback, frame

        cv2.putText(frame, f"Knee: {int(knee_angle)}", display_knee_pt,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Hip: {int(hip_angle)}", display_hip_pt,
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

        # Rep counting logic
        if (knee_angle < self.knee_angle_down_threshold and 
            hip_angle < self.hip_angle_down_threshold and 
            self.stage == "UP"):
            self.stage = "DOWN"
            self.feedback = "Squatting Down"
            # --- DEBUG PRINT ---
            # print(f"    --> Stage: DOWN (Knee: {knee_angle:.1f} < {self.knee_angle_down_threshold}, Hip: {hip_angle:.1f} < {self.hip_angle_down_threshold})")
            # --- END DEBUG ---
        elif (knee_angle > self.knee_angle_up_threshold and 
              hip_angle > self.hip_angle_up_threshold and 
              self.stage == "DOWN"):
            self.stage = "UP"
            self.reps += 1
            self.feedback = "Standing Up - Rep Counted!"
            # --- DEBUG PRINT ---
            # print(f"    --> Stage: UP, REP! (Knee: {knee_angle:.1f} > {self.knee_angle_up_threshold}, Hip: {hip_angle:.1f} > {self.hip_angle_up_threshold})")
            # --- END DEBUG ---
        elif self.stage == "UP":
            self.feedback = "Lower your hips"
        elif self.stage == "DOWN":
            self.feedback = "Stand up fully"

        return self.reps, self.feedback, frame