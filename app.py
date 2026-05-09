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

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Smart Attendance</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial; background: #1a1a2e; color: white; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; }
        h1 { color: #e94560; margin-bottom: 10px; font-size: 28px; }
        p { color: #aaa; margin-bottom: 20px; }
        .card { background: #16213e; border-radius: 16px; padding: 30px; width: 100%; max-width: 500px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: 1px solid #0f3460; background: #0f3460; color: white; font-size: 16px; }
        button { width: 100%; padding: 14px; margin: 8px 0; border-radius: 8px; border: none; font-size: 16px; cursor: pointer; font-weight: bold; transition: all 0.3s; }
        .btn-primary { background: #e94560; color: white; }
        .btn-primary:hover { background: #c73652; }
        .btn-secondary { background: #0f3460; color: white; }
        .btn-secondary:hover { background: #1a4a7a; }
        video { width: 100%; border-radius: 12px; margin: 10px 0; }
        #status { font-size: 18px; margin: 15px 0; padding: 12px; border-radius: 8px; text-align: center; display: none; }
        .success { background: #1a472a; color: #51cf66; }
        .error { background: #4a1a1a; color: #ff6b6b; }
        .info { background: #1a3a4a; color: #74c0fc; }
        #counter { font-size: 48px; font-weight: bold; color: #e94560; text-align: center; display: none; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { flex: 1; padding: 12px; border-radius: 8px; border: none; cursor: pointer; font-size: 15px; font-weight: bold; }
        .tab.active { background: #e94560; color: white; }
        .tab.inactive { background: #0f3460; color: #aaa; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th { background: #e94560; padding: 10px; text-align: left; }
        td { padding: 10px; border-bottom: 1px solid #0f3460; }
        .present { color: #51cf66; font-weight: bold; }
        .late { color: #ffd43b; font-weight: bold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>📸 Smart Attendance</h1>
        <p>AI-powered face recognition attendance system</p>

        <div class="tabs">
            <button class="tab active" onclick="showTab('attend')">Mark Attendance</button>
            <button class="tab inactive" onclick="showTab('register')">Register</button>
            <button class="tab inactive" onclick="showTab('records')">Records</button>
        </div>

        <!-- Attendance Tab -->
        <div id="attend-tab">
            <p>Look straight at camera and click the button</p>
            <video id="video1" autoplay playsinline></video>
            <canvas id="canvas1" style="display:none"></canvas>
            <div id="counter1" class="counter"></div>
            <button class="btn-primary" onclick="markAttendance()">📷 Mark My Attendance</button>
            <div id="status1" class="status"></div>
        </div>

        <!-- Register Tab -->
        <div id="register-tab" style="display:none">
            <p>First time? Register yourself here</p>
            <input type="text" id="name" placeholder="Full Name (e.g. Priyanshu Singh)">
            <input type="text" id="rollno" placeholder="Roll Number (e.g. 125EC0063)">
            <video id="video2" autoplay playsinline></video>
            <canvas id="canvas2" style="display:none"></canvas>
            <div id="counter2" style="display:none; font-size:48px; font-weight:bold; color:#e94560; text-align:center;"></div>
            <button class="btn-primary" onclick="startRegistration()">📸 Take 3 Photos & Register</button>
            <div id="status2" class="status"></div>
        </div>

        <!-- Records Tab -->
        <div id="records-tab" style="display:none">
            <h3>Today's Attendance</h3>
            <div id="records-table">{{ table|safe }}</div>
        </div>
    </div>

    <script>
        // Start cameras
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                document.getElementById('video1').srcObject = stream;
                document.getElementById('video2').srcObject = stream.clone ? stream.clone() : stream;
            })
            .catch(err => {
                alert('Camera access denied! Please allow camera and refresh.');
            });

        function showTab(tab) {
            document.getElementById('attend-tab').style.display = 'none';
            document.getElementById('register-tab').style.display = 'none';
            document.getElementById('records-tab').style.display = 'none';
            document.getElementById(tab + '-tab').style.display = 'block';
            document.querySelectorAll('.tab').forEach(t => { t.className = 'tab inactive'; });
            event.target.className = 'tab active';
        }

        function capturePhoto(videoId, canvasId) {
            const video = document.getElementById(videoId);
            const canvas = document.getElementById(canvasId);
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            return canvas.toDataURL('image/jpeg');
        }

        function showStatus(id, message, type) {
            const el = document.getElementById(id);
            el.style.display = 'block';
            el.textContent = message;
            el.className = 'status ' + type;
        }

        function markAttendance() {
            showStatus('status1', '⏳ Scanning your face...', 'info');
            const photo = capturePhoto('video1', 'canvas1');
            fetch('/mark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: photo })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showStatus('status1', '✅ ' + data.name + ' (' + data.roll_no + ') marked ' + data.status + '!', 'success');
                } else {
                    showStatus('status1', '❌ Face not recognized! Please register first.', 'error');
                }
            });
        }

        function startRegistration() {
            const name = document.getElementById('name').value.trim();
            const rollno = document.getElementById('rollno').value.trim();
            if (!name || !rollno) {
                showStatus('status2', '⚠️ Please enter your name and roll number!', 'error');
                return;
            }
            showStatus('status2', '📸 Taking 3 photos automatically...', 'info');
            const photos = [];
            let count = 3;
            const counter = document.getElementById('counter2');
            counter.style.display = 'block';

            function takePhoto() {
                if (count === 0) {
                    counter.style.display = 'none';
                    showStatus('status2', '⏳ Registering...', 'info');
                    fetch('/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, rollno, photos })
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success) {
                            showStatus('status2', '✅ Registered successfully! You can now mark attendance.', 'success');
                        } else {
                            showStatus('status2', '❌ Registration failed. Try again.', 'error');
                        }
                    });
                    return;
                }
                counter.textContent = count;
                photos.push(capturePhoto('video2', 'canvas2'));
                count--;
                setTimeout(takePhoto, 1000);
            }
            takePhoto();
        }
    </script>
</body>
</html>
"""

def get_table_html():
    if not os.path.exists(ATTENDANCE_FILE):
        return "<p style='color:#aaa'>No attendance records yet.</p>"
    df = pd.read_csv(ATTENDANCE_FILE)
    if df.empty:
        return "<p style='color:#aaa'>No attendance records yet.</p>"
    rows = ""
    for _, row in df.iterrows():
        css = "present" if str(row.get("status","")) == "present" else "late"
        rows += f"<tr><td>{row.get('roll_no','')}</td><td>{row.get('name','')}</td><td>{row.get('timestamp','')}</td><td class='{css}'>{row.get('status','')}</td></tr>"
    return f"<table><tr><th>Roll No</th><th>Name</th><th>Time</th><th>Status</th></tr>{rows}</table>"

@app.route("/")
def index():
    return render_template_string(HTML, table=get_table_html())

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    name = data["name"].strip()
    rollno = data["rollno"].strip()
    photos = data["photos"]

    folder = os.path.join(STUDENTS_DB, f"{rollno}_{name}")
    os.makedirs(folder, exist_ok=True)

    for i, photo_data in enumerate(photos):
        img_bytes = base64.b64decode(photo_data.split(",")[1])
        img_array = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        cv2.imwrite(os.path.join(folder, f"photo{i+1}.jpg"), frame)

    return jsonify({"success": True})

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
            parts = folder_name.split("_")
            roll_no = parts[0]
            name = "_".join(parts[1:])
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

            new_row = pd.DataFrame([{
                "roll_no": roll_no,
                "name": name,
                "timestamp": timestamp,
                "status": "present"
            }])

            if os.path.exists(ATTENDANCE_FILE):
                existing = pd.read_csv(ATTENDANCE_FILE)
                df = pd.concat([existing, new_row], ignore_index=True)
            else:
                df = new_row

            df.to_csv(ATTENDANCE_FILE, index=False)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"success": True, "name": name, "roll_no": roll_no, "status": "present"})
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"success": False})

    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"success": False})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host="0.0.0.0", port=port)
