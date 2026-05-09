from flask import Flask, render_template_string, request, jsonify
from deepface import DeepFace
import pandas as pd
import base64
import os
import numpy as np
import cv2
from datetime import datetime

app = Flask(__name__)

STUDENTS_DB = "students/"
ATTENDANCE_FILE = "attendance.csv"
CLASS_START = "09:00"
LATE_THRESHOLD_MINS = 10

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Attendance</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 30px; background: #f0f0f0; }
        h1 { color: #333; }
        #video { border-radius: 12px; width: 400px; }
        button { padding: 12px 30px; font-size: 16px; margin: 10px;
                 background: #4CAF50; color: white; border: none;
                 border-radius: 8px; cursor: pointer; }
        button:hover { background: #45a049; }
        #status { font-size: 20px; margin-top: 20px; font-weight: bold; }
        #result { margin-top: 10px; font-size: 16px; color: #555; }
        table { margin: 30px auto; border-collapse: collapse; background: white;
                border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        th { background: #4CAF50; color: white; padding: 12px 20px; }
        td { padding: 10px 20px; border-bottom: 1px solid #eee; }
        .present { color: green; font-weight: bold; }
        .late { color: orange; font-weight: bold; }
    </style>
</head>
<body>
    <h1>📸 Smart Attendance System</h1>
    <p>Look straight into the camera and click Mark Attendance</p>

    <video id="video" autoplay playsinline></video>
    <canvas id="canvas" style="display:none"></canvas>
    <br>
    <button onclick="markAttendance()">📷 Mark My Attendance</button>

    <div id="status"></div>
    <div id="result"></div>

    <h2>Today's Attendance</h2>
    <div id="table">{{ table|safe }}</div>

    <script>
        // Start webcam automatically
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                document.getElementById('video').srcObject = stream;
            })
            .catch(err => {
                document.getElementById('status').innerHTML = 
                '❌ Camera access denied. Please allow camera and refresh.';
                document.getElementById('status').style.color = 'red';
            });

        function markAttendance() {
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            const photo = canvas.toDataURL('image/jpeg');

            document.getElementById('status').innerHTML = '⏳ Scanning your face...';
            document.getElementById('status').style.color = '#333';

            fetch('/mark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: photo })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('status').innerHTML = 
                        '✅ ' + data.name + ' marked ' + data.status + '!';
                    document.getElementById('status').style.color = 'green';
                    setTimeout(() => location.reload(), 2000);
                } else {
                    document.getElementById('status').innerHTML = 
                        '❌ Face not recognized. Try again!';
                    document.getElementById('status').style.color = 'red';
                }
            });
        }
    </script>
</body>
</html>
"""

def get_status(current_time):
    start = datetime.strptime(CLASS_START, "%H:%M").replace(
        year=current_time.year,
        month=current_time.month,
        day=current_time.day
    )
    diff_minutes = (current_time - start).total_seconds() / 60
    if diff_minutes <= LATE_THRESHOLD_MINS:
        return "present"
    else:
        return "late"

def get_table_html():
    if not os.path.exists(ATTENDANCE_FILE):
        return "<p>No attendance records yet.</p>"
    df = pd.read_csv(ATTENDANCE_FILE)
    if df.empty:
        return "<p>No attendance records yet.</p>"
    rows = ""
    for _, row in df.iterrows():
        css = "present" if row.get("status") == "present" else "late"
        rows += f"<tr><td>{row.get('roll_no','')}</td><td>{row.get('name','')}</td><td>{row.get('timestamp','')}</td><td class='{css}'>{row.get('status','')}</td></tr>"
    return f"<table><tr><th>Roll No</th><th>Name</th><th>Time</th><th>Status</th></tr>{rows}</table>"

@app.route("/")
def index():
    return render_template_string(HTML, table=get_table_html())

@app.route("/mark", methods=["POST"])
def mark():
    data = request.json
    image_data = data["image"].split(",")[1]
    img_bytes = base64.b64decode(image_data)
    img_array = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    temp_path = "temp_web.jpg"
    cv2.imwrite(temp_path, frame)

    try:
        results = DeepFace.find(
            img_path=temp_path,
            db_path=STUDENTS_DB,
            model_name="Facenet512",
            enforce_detection=False
        )

        if results and len(results[0]) > 0:
            identity_path = results[0].iloc[0]["identity"]
            folder_name = identity_path.split(os.sep)[-2]
            roll_no = folder_name.split("_")[0]
            name = "_".join(folder_name.split("_")[1:])
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            status = get_status(now)

            new_row = pd.DataFrame([{
                "roll_no": roll_no,
                "name": name,
                "timestamp": timestamp,
                "status": status
            }])

            if os.path.exists(ATTENDANCE_FILE):
                existing = pd.read_csv(ATTENDANCE_FILE)
                df = pd.concat([existing, new_row], ignore_index=True)
            else:
                df = new_row

            df.to_csv(ATTENDANCE_FILE, index=False)
            os.remove(temp_path)
            return jsonify({"success": True, "name": name, "status": status})
        else:
            os.remove(temp_path)
            return jsonify({"success": False})

    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"success": False})

if __name__ == "__main__":
import os
port = int(os.environ.get("PORT", 8080))
app.run(debug=False, host="0.0.0.0", port=port)
