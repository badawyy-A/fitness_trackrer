# fitness_tracker/exercises/bicep_curl.py
import cv2
import numpy as np
from utils.tracker import calculate_angle

class BicepCurlTracker:
    def __init__(self):
        self.reps = 0
        self.stage = "DOWN"  # Can be "UP" (flexed) or "DOWN" (extended)
        self.feedback = "Start Bicep Curls"
        
        # Thresholds (VERY IMPORTANT - TUNE THESE)
        self.elbow_angle_up_threshold = 70   # Max angle for elbow when flexed (more bent)
        self.elbow_angle_down_threshold = 150 # Min angle for elbow when extended (straighter)

    def process_frame(self, keypoints_xy, frame):
        if keypoints_xy.shape[0] < 17:
            self.feedback = "Not all keypoints visible"
            return self.reps, self.feedback, frame

        r_shoulder = keypoints_xy[6]
        r_elbow = keypoints_xy[8]
        r_wrist = keypoints_xy[10]
        
        l_shoulder = keypoints_xy[5]
        l_elbow = keypoints_xy[7]
        l_wrist = keypoints_xy[9]

        right_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
        left_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
        
        elbow_angle = None
        arm_side_points = None 

        if right_elbow_angle is not None: # Prioritize right arm
            elbow_angle = right_elbow_angle
            arm_side_points = (r_shoulder, r_elbow, r_wrist)
            # cv2.putText(frame, "Tracking: Right Arm", (10, frame.shape[0] - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1, cv2.LINE_AA)
        elif left_elbow_angle is not None: # Fallback to left arm
            elbow_angle = left_elbow_angle
            arm_side_points = (l_shoulder, l_elbow, l_wrist)
            # cv2.putText(frame, "Tracking: Left Arm", (10, frame.shape[0] - 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1, cv2.LINE_AA)
        
        # --- DEBUG PRINT ---
        # print(f"Bicep Curl - Stage: {self.stage}, Elbow: {elbow_angle}, Reps: {self.reps}")
        # --- END DEBUG ---

        if elbow_angle is None or arm_side_points is None:
            self.feedback = "Ensure at least one elbow is clearly visible."
            return self.reps, self.feedback, frame

        cv2.putText(frame, f"Elbow: {int(elbow_angle)}", 
                    (int(arm_side_points[1][0] + 10), int(arm_side_points[1][1])), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

        # Rep counting logic
        if elbow_angle < self.elbow_angle_up_threshold and self.stage == "DOWN":
            self.stage = "UP"
            self.feedback = "Curling Up"
            # --- DEBUG PRINT ---
            # print(f"    --> Stage: UP (Elbow: {elbow_angle:.1f} < {self.elbow_angle_up_threshold})")
            # --- END DEBUG ---
        elif elbow_angle > self.elbow_angle_down_threshold and self.stage == "UP":
            self.stage = "DOWN"
            self.reps += 1
            self.feedback = "Lowering - Rep Counted!"
            # --- DEBUG PRINT ---
            # print(f"    --> Stage: DOWN, REP! (Elbow: {elbow_angle:.1f} > {self.elbow_angle_down_threshold})")
            # --- END DEBUG ---
        elif self.stage == "DOWN":
            self.feedback = "Curl Up"
        elif self.stage == "UP":
            self.feedback = "Lower Down"

        return self.reps, self.feedback, frame