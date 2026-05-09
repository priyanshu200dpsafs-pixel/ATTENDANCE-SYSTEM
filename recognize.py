import cv2
from deepface import DeepFace
import pandas as pd
from datetime import datetime
import os

STUDENTS_DB = "students/"          # folder with student photos
ATTENDANCE_FILE = "attendance.csv"
CLASS_START = "09:00"              # 24hr format
LATE_THRESHOLD_MINS = 10           # must arrive within 10 min
SCAN_INTERVAL_MINS = 20            # scan every 20 minutes

def capture_frame():
    """Grab one frame from the classroom camera."""
    cap = cv2.VideoCapture(0)
    # Give camera 2 seconds to warm up
    for i in range(10):
        ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Could not read from camera")
        return None
    return frame

def scan_and_mark():
    """Main function: capture, recognize all faces, update attendance."""
    frame = capture_frame()
    if frame is None:
        return

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    # Save frame temporarily for DeepFace to process
    temp_path = "temp_frame.jpg"
    cv2.imwrite(temp_path, frame)

    try:
        # Find all faces in the frame and match to database
        results = DeepFace.find(
            img_path=temp_path,
            db_path=STUDENTS_DB,
            model_name="Facenet512",      # accurate model
            enforce_detection=False        # don't crash if no face found
        )
    except Exception as e:
        print(f"Recognition error: {e}")
        return

    recognized_students = []
    for result_df in results:
        if len(result_df) > 0:
            # Extract student ID from folder name (e.g. ROL001_Arjun_Sharma)
            identity_path = result_df.iloc[0]["identity"]
            folder_name = identity_path.split(os.sep)[-2]
            roll_no = folder_name.split("_")[0]
            name = "_".join(folder_name.split("_")[1:])
            recognized_students.append({
                "roll_no": roll_no,
                "name": name,
                "timestamp": timestamp,
                "status": get_status(now)
            })

    # Save to CSV
    df = pd.DataFrame(recognized_students)
    if os.path.exists(ATTENDANCE_FILE):
        df.to_csv(ATTENDANCE_FILE, mode='a', header=False, index=False)
    else:
        df.to_csv(ATTENDANCE_FILE, index=False)

    print(f"[{timestamp}] Marked {len(recognized_students)} students present")
    os.remove(temp_path)

def get_status(current_time):
    """Determine if student is on time, late, or checked for early exit."""
    start = datetime.strptime(CLASS_START, "%H:%M").replace(
        year=current_time.year,
        month=current_time.month,
        day=current_time.day
    )
    diff_minutes = (current_time - start).total_seconds() / 60

    if diff_minutes <= LATE_THRESHOLD_MINS:
        return "present"
    elif diff_minutes <= 0:
        return "present"
    else:
        return "late"

if __name__ == "__main__":
    scan_and_mark()