# fitness_tracker/main.py
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
import numpy as np

from exercises import EXERCISE_TRACKERS

class FitnessTrackerApp:
    def __init__(self, master):
        self.master = master
        master.title("Fitness Tracker")
        master.geometry("1000x750") 

        self.model_path = 'yolov8s-pose.pt' 
        try:
            self.model = YOLO(self.model_path)
        except Exception as e:
            messagebox.showerror("Model Error", f"Failed to load YOLO model: {e}\nEnsure '{self.model_path}' is accessible.")
            master.destroy()
            return

        self.cap = None
        self.tracking = False
        self.current_exercise_name = None
        self.exercise_tracker = None

        # To store current rep count and feedback for OpenCV drawing
        self.current_reps_val = 0
        self.current_feedback_str = "Select an exercise and start tracking."

        # --- GUI Elements ---
        # Top Frame for controls - REMAINS
        self.control_frame = ttk.Frame(master, padding="10")
        self.control_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(self.control_frame, text="Select Exercise:").pack(side=tk.LEFT, padx=5)
        self.exercise_var = tk.StringVar()
        self.exercise_options = list(EXERCISE_TRACKERS.keys())
        self.exercise_menu = ttk.Combobox(self.control_frame, textvariable=self.exercise_var, 
                                          values=self.exercise_options, state="readonly")
        if self.exercise_options:
            self.exercise_menu.current(0)
        self.exercise_menu.pack(side=tk.LEFT, padx=5)
        self.exercise_menu.bind("<<ComboboxSelected>>", self.on_exercise_select)

        self.track_button = ttk.Button(self.control_frame, text="Start Tracking", command=self.toggle_tracking)
        self.track_button.pack(side=tk.LEFT, padx=5)

        # Video display - takes up space below control_frame
        self.video_label = ttk.Label(master)
        self.video_label.pack(pady=10, expand=True, fill=tk.BOTH) 

        # REMOVED: Bottom Frame for feedback (feedback_frame and its labels)
        # self.feedback_frame = ttk.Frame(master, padding="10")
        # self.feedback_frame.pack(side=tk.BOTTOM, fill=tk.X)
        # self.reps_label_text = tk.StringVar(value="Reps: 0")
        # ttk.Label(self.feedback_frame, textvariable=self.reps_label_text, font=("Arial", 16)).pack(side=tk.LEFT, padx=20)
        # self.feedback_label_text = tk.StringVar(value="Feedback: Select an exercise and start tracking.")
        # ttk.Label(self.feedback_frame, textvariable=self.feedback_label_text, font=("Arial", 14)).pack(side=tk.LEFT, padx=20)

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        if self.exercise_options:
            self.on_exercise_select() 

    def on_exercise_select(self, event=None):
        if self.tracking:
            messagebox.showwarning("Tracking Active", "Please stop tracking before changing exercises.")
            if self.current_exercise_name:
                 self.exercise_var.set(self.current_exercise_name)
            return

        selected_exercise = self.exercise_var.get()
        if selected_exercise and selected_exercise in EXERCISE_TRACKERS:
            self.current_exercise_name = selected_exercise
            self.exercise_tracker = EXERCISE_TRACKERS[selected_exercise]() # Re-initialize
            
            self.current_reps_val = 0
            self.current_feedback_str = f"Ready for {selected_exercise}"
            print(f"Selected exercise: {selected_exercise}")
        else:
            self.exercise_tracker = None
            self.current_exercise_name = None
            self.current_feedback_str = "Please select a valid exercise."


    def toggle_tracking(self):
        if not self.current_exercise_name:
            messagebox.showerror("Error", "Please select an exercise first!")
            return

        if self.tracking: # --- STOP TRACKING ---
            self.tracking = False
            self.track_button.config(text="Start Tracking")
            self.exercise_menu.config(state="readonly") # Re-enable combobox
            if self.cap:
                self.cap.release()
                self.cap = None
            
            self.current_feedback_str = f"Tracking stopped for {self.current_exercise_name}."
            # Display one last frame with the "stopped" message if video label is still configured
            # Or clear the video label
            # self.video_label.config(image='')
            # self.video_label.image = None


        else: # --- START TRACKING ---
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Camera Error", "Cannot open webcam.")
                self.cap = None
                return
            
            if self.current_exercise_name in EXERCISE_TRACKERS:
                 self.exercise_tracker = EXERCISE_TRACKERS[self.current_exercise_name]()
            else: 
                messagebox.showerror("Error", "Invalid exercise selected.")
                return

            self.current_reps_val = 0 # Reset reps for the new session
            self.current_feedback_str = f"Tracking {self.current_exercise_name}..."

            self.tracking = True
            self.track_button.config(text="Stop Tracking")
            self.exercise_menu.config(state="disabled") # Disable combobox while tracking
            
            self.update_frame()

    def draw_text_with_background(self, frame, text, position, font_scale=0.7, text_color=(255,255,255), bg_color=(0,0,0), thickness=2, padding=5):
        """Draws text with a contrasting background rectangle for better visibility."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        
        rect_x1 = position[0] - padding
        rect_y1 = position[1] - text_height - padding - baseline // 2 
        rect_x2 = position[0] + text_width + padding
        rect_y2 = position[1] + padding + baseline // 2

        rect_x1 = max(0, rect_x1)
        rect_y1 = max(0, rect_y1)
        rect_x2 = min(frame.shape[1], rect_x2)
        rect_y2 = min(frame.shape[0], rect_y2)

        if bg_color is not None:
             cv2.rectangle(frame, (rect_x1, rect_y1), (rect_x2, rect_y2), bg_color, -1)
        
        cv2.putText(frame, text, position, font, font_scale, text_color, thickness, cv2.LINE_AA)


    def update_frame(self):
        if not self.cap or not self.cap.isOpened(): # Check if tracking should even run
            if self.tracking: # If it was supposed to run but cap is bad, stop it.
                self.toggle_tracking() # This will set self.tracking to False
            return

        ret, frame = self.cap.read()
        if not ret:
            print("Failed to grab frame")
            if self.tracking: self.master.after(10, self.update_frame)
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model(frame_rgb, verbose=False, conf=0.55) 
        
        annotated_frame = frame.copy() 

        temp_feedback_for_frame = self.current_feedback_str # Use existing feedback if no new one

        if self.tracking and results and results[0].keypoints and results[0].keypoints.xy.numel() > 0:
            keypoints_xy = results[0].keypoints.xy[0].cpu().numpy()
            keypoints_conf = results[0].keypoints.conf[0].cpu().numpy() if results[0].keypoints.conf is not None else np.ones(keypoints_xy.shape[0])

            for i, (x, y) in enumerate(keypoints_xy):
                if keypoints_conf[i] > 0.5: 
                     cv2.circle(annotated_frame, (int(x), int(y)), 4, (0, 255, 0), -1)
            
            if self.exercise_tracker:
                reps, feedback, processed_frame = self.exercise_tracker.process_frame(keypoints_xy, annotated_frame)
                self.current_reps_val = reps 
                temp_feedback_for_frame = feedback # Get feedback from tracker
                display_frame = processed_frame
            else:
                temp_feedback_for_frame = "Error: No exercise logic."
                display_frame = annotated_frame
        elif self.tracking: # Still tracking but no person detected
            temp_feedback_for_frame = "No person detected / keypoints unclear."
            display_frame = annotated_frame # Show annotated frame even if no person
        else: # Not tracking, just show raw frame or last feedback
            display_frame = frame

        self.current_feedback_str = temp_feedback_for_frame # Update the main feedback string

        # --- Draw Reps and Feedback directly on the frame using OpenCV ---
        # This will be drawn whether tracking is active or just stopped (to show final message)
        reps_text = f"Reps: {self.current_reps_val}"
        self.draw_text_with_background(display_frame, reps_text, (20, 40), font_scale=1, text_color=(255,255,255), bg_color=(0,0,0), thickness=2)

        feedback_text_to_draw = f"Feedback: {self.current_feedback_str}"
        font_scale_feedback = 0.6
        thickness_feedback = 1
        y_offset_feedback = 75
        line_height = int(cv2.getTextSize("Tg", cv2.FONT_HERSHEY_SIMPLEX, font_scale_feedback, thickness_feedback)[0][1] * 1.5)

        words = feedback_text_to_draw.split(' ')
        current_line = ""
        max_line_width = display_frame.shape[1] - 40 # 20px padding on each side
        for word in words:
            test_line = f"{current_line} {word}".strip()
            (text_width, _), _ = cv2.getTextSize(test_line, cv2.FONT_HERSHEY_SIMPLEX, font_scale_feedback, thickness_feedback)
            if text_width < max_line_width:
                current_line = test_line
            else:
                self.draw_text_with_background(display_frame, current_line, (20, y_offset_feedback), font_scale=font_scale_feedback, text_color=(255,255,0), bg_color=(0,0,0), thickness=thickness_feedback)
                y_offset_feedback += line_height
                current_line = word
        if current_line: 
            self.draw_text_with_background(display_frame, current_line, (20, y_offset_feedback), font_scale=font_scale_feedback, text_color=(255,255,0), bg_color=(0,0,0), thickness=thickness_feedback)

        # Convert frame for Tkinter
        img = Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB))
        
        label_width = self.video_label.winfo_width()
        label_height = self.video_label.winfo_height()

        if label_width > 1 and label_height > 1 : 
            img_width, img_height = img.size
            if img_width == 0 or img_height == 0:
                 if self.tracking: self.master.after(10, self.update_frame)
                 return

            aspect_ratio = img_width / img_height
            
            new_width = label_width
            new_height = int(new_width / aspect_ratio)
            
            if new_height > label_height:
                new_height = label_height
                new_width = int(new_height * aspect_ratio)
            
            if new_width > 0 and new_height > 0:
                 img = img.resize((new_width, new_height), Image.LANCZOS)

        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.config(image=imgtk)

        if self.tracking: # Continue updating only if tracking
            self.master.after(10, self.update_frame)
        elif not self.cap : # If tracking stopped and cap is released, ensure last frame is displayed
             #This path is for displaying the "Tracking stopped" message on the last frame
             pass


    def on_close(self):
        print("Closing application...")
        self.tracking = False 
        if self.cap:
            self.cap.release()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FitnessTrackerApp(root)
    root.mainloop()