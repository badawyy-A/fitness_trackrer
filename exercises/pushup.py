# fitness_tracker/exercises/pushup.py
import cv2
import numpy as np
from utils.tracker import calculate_angle

class PushupTracker:
    def __init__(self):
        self.reps = 0
        self.stage = "UP"  # Can be "UP" or "DOWN"
        self.feedback = "Start Push-ups"
        
        # Thresholds (VERY IMPORTANT - TUNE THESE)
        self.elbow_angle_down_threshold = 95  # Max angle for elbow when down (more bent)
        self.elbow_angle_up_threshold = 155 # Min angle for elbow when up (straighter)
        self.hip_angle_straight_threshold = 150 # Min angle to keep body straight

    def process_frame(self, keypoints_xy, frame):
        if keypoints_xy.shape[0] < 17:
            self.feedback = "Not all keypoints visible"
            return self.reps, self.feedback, frame

        r_shoulder = keypoints_xy[6]
        r_elbow = keypoints_xy[8]
        r_wrist = keypoints_xy[10]
        r_hip = keypoints_xy[12]
        r_knee = keypoints_xy[14]

        l_shoulder = keypoints_xy[5]
        l_elbow = keypoints_xy[7]
        l_wrist = keypoints_xy[9]
        l_hip = keypoints_xy[11]
        l_knee = keypoints_xy[13]
        
        right_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
        right_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee)
        
        left_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
        left_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)

        elbow_angle = None
        hip_angle = None

        if right_elbow_angle is not None and left_elbow_angle is not None:
            elbow_angle = (right_elbow_angle + left_elbow_angle) / 2
        elif right_elbow_angle is not None:
            elbow_angle = right_elbow_angle
        elif left_elbow_angle is not None:
            elbow_angle = left_elbow_angle
        
        if right_hip_angle is not None and left_hip_angle is not None:
            hip_angle = (right_hip_angle + left_hip_angle) / 2
        elif right_hip_angle is not None:
            hip_angle = right_hip_angle
        elif left_hip_angle is not None:
            hip_angle = left_hip_angle

        # --- DEBUG PRINT ---
        # print(f"Pushup - Stage: {self.stage}, Elbow: {elbow_angle}, Hip: {hip_angle}, Reps: {self.reps}")
        # --- END DEBUG ---

        display_elbow_pt = r_elbow if right_elbow_angle is not None else (l_elbow if left_elbow_angle is not None else None)
        display_hip_pt = r_hip if right_hip_angle is not None else (l_hip if left_hip_angle is not None else None)

        if display_elbow_pt is not None and elbow_angle is not None:
            cv2.putText(frame, f"Elbow: {int(elbow_angle)}", 
                        (int(display_elbow_pt[0] + 10), int(display_elbow_pt[1])), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)
        if display_hip_pt is not None and hip_angle is not None:
            cv2.putText(frame, f"Hip: {int(hip_angle)}", 
                        (int(display_hip_pt[0] + 10), int(display_hip_pt[1])), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2, cv2.LINE_AA)

        if elbow_angle is None or hip_angle is None:
            self.feedback = "Ensure arms and hips are clearly visible."
            return self.reps, self.feedback, frame

        # Rep counting logic
        if hip_angle >= self.hip_angle_straight_threshold: # Body should be relatively straight
            # --- DEBUG PRINT ---
            # print(f"  Body straight (Hip: {hip_angle:.1f} >= {self.hip_angle_straight_threshold})")
            # --- END DEBUG ---
            if elbow_angle < self.elbow_angle_down_threshold and self.stage == "UP":
                self.stage = "DOWN"
                self.feedback = "Pushing Down"
                # --- DEBUG PRINT ---
                # print(f"    --> Stage: DOWN (Elbow: {elbow_angle:.1f} < {self.elbow_angle_down_threshold})")
                # --- END DEBUG ---
            elif elbow_angle > self.elbow_angle_up_threshold and self.stage == "DOWN":
                self.stage = "UP"
                self.reps += 1
                self.feedback = "Pushing Up - Rep Counted!"
                # --- DEBUG PRINT ---
                # print(f"    --> Stage: UP, REP! (Elbow: {elbow_angle:.1f} > {self.elbow_angle_up_threshold})")
                # --- END DEBUG ---
            elif self.stage == "UP":
                self.feedback = "Lower your chest"
            elif self.stage == "DOWN":
                 self.feedback = "Extend your arms"
        else:
            self.feedback = "Keep your body straight!"
            # --- DEBUG PRINT ---
            # print(f"  Body NOT straight (Hip: {hip_angle:.1f} < {self.hip_angle_straight_threshold})")
            # --- END DEBUG ---
            # self.stage = "UP" # Optional: Reset stage if body not straight to prevent count on recovery

        return self.reps, self.feedback, frame