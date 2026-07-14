from flask import Flask, render_template, request, redirect
import os
import cv2
import sqlite3
from inference_sdk import InferenceHTTPClient

app = Flask(__name__)

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="BgHFp2MKPApEAjXl9joR"
)

UPLOAD_FOLDER = "static"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------- DATABASE ----------
conn = sqlite3.connect("potholes.db")
c = conn.cursor()
c.execute("""CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude TEXT,
                longitude TEXT,
                pothole_count INTEGER,
                severity TEXT
            )""")
conn.commit()
conn.close()


# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    image_path = None
    pothole_count = 0
    severity = None
    lat = None
    lon = None

    if request.method == "POST":
        file = request.files["file"]
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        lat = request.form.get("lat")
        lon = request.form.get("lon")

        result = CLIENT.infer(file_path, model_id="pothole-detection-bfeeg-hp6tw/1")
        image = cv2.imread(file_path)

        for prediction in result["predictions"]:
            x = int(prediction["x"])
            y = int(prediction["y"])
            w = int(prediction["width"])
            h = int(prediction["height"])

            x1 = int(x - w / 2)
            y1 = int(y - h / 2)
            x2 = int(x + w / 2)
            y2 = int(y + h / 2)

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)
            pothole_count += 1

        output_path = os.path.join("static", "output.jpg")
        cv2.imwrite(output_path, image)
        image_path = output_path

        if pothole_count <= 2:
            severity = "Low"
        elif pothole_count <= 5:
            severity = "Medium"
        else:
            severity = "High"

        conn = sqlite3.connect("potholes.db")
        c = conn.cursor()
        c.execute("INSERT INTO reports (latitude, longitude, pothole_count, severity) VALUES (?, ?, ?, ?)",
                  (lat, lon, pothole_count, severity))
        conn.commit()
        conn.close()

    return render_template("index.html",
                           image=image_path,
                           count=pothole_count,
                           severity=severity,
                           lat=lat,
                           lon=lon)


# ---------------- HISTORY WITH FILTER + SEARCH ----------------
@app.route("/history")
def history():
    filter_severity = request.args.get("severity")
    search_query = request.args.get("search")

    conn = sqlite3.connect("potholes.db")
    c = conn.cursor()

    query = "SELECT * FROM reports WHERE 1=1"
    params = []

    if filter_severity and filter_severity != "All":
        query += " AND severity=?"
        params.append(filter_severity)

    if search_query:
        query += " AND (latitude LIKE ? OR longitude LIKE ?)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")

    query += " ORDER BY id DESC"

    c.execute(query, params)
    reports = c.fetchall()

    total_reports = len(reports)
    total_potholes = sum(r[3] for r in reports)
    high_count = sum(1 for r in reports if r[4] == "High")
    medium_count = sum(1 for r in reports if r[4] == "Medium")
    low_count = sum(1 for r in reports if r[4] == "Low")

    conn.close()

    return render_template("history.html",
                           reports=reports,
                           total_reports=total_reports,
                           total_potholes=total_potholes,
                           high_count=high_count,
                           medium_count=medium_count,
                           low_count=low_count,
                           selected_severity=filter_severity,
                           search_query=search_query)


# ---------------- DELETE ----------------
@app.route("/delete/<int:report_id>")
def delete_report(report_id):
    conn = sqlite3.connect("potholes.db")
    c = conn.cursor()
    c.execute("DELETE FROM reports WHERE id=?", (report_id,))
    conn.commit()
    conn.close()
    return redirect("/history")


if __name__ == "__main__":
    app.run(debug=True)