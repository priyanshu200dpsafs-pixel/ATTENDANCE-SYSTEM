from flask import Flask, render_template_string
import pandas as pd

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html><html><body>
<h2>Attendance Records</h2>
<table border="1" cellpadding="8">
<tr><th>Roll No</th><th>Name</th><th>Time</th><th>Status</th></tr>
{% for _, row in df.iterrows() %}
<tr>
  <td>{{ row.roll_no }}</td>
  <td>{{ row.name }}</td>
  <td>{{ row.timestamp }}</td>
  <td style="color: {{'green' if row.status == 'present' else 'orange'}}">{{ row.status }}</td>
</tr>
{% endfor %}
</table></body></html>
"""

@app.route("/")
def index():
    df = pd.read_csv("attendance.csv")
    return render_template_string(TEMPLATE, df=df)

if __name__ == "__main__":
    app.run(debug=True, port=8080)