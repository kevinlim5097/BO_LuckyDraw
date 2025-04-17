from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import random
import csv
from datetime import datetime

app = Flask(__name__)

DATA_FILE = "data.json"
CSV_FILE = "results.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"items": [], "history": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/run")
def run_wheel():
    return render_template("wheel.html")

@app.route("/api/items", methods=["GET", "POST"])
def api_items():
    data = load_data()
    if request.method == "POST":
        item = request.json.get("item")
        if item:
            data["items"].append(item)
            save_data(data)
    return jsonify(data["items"])

@app.route("/api/items/<item>", methods=["DELETE"])
def delete_item(item):
    data = load_data()
    if item in data["items"]:
        data["items"].remove(item)
        save_data(data)
        return jsonify({"message": "Item deleted successfully"}), 200
    else:
        return jsonify({"error": "Item not found"}), 404

@app.route("/api/spin", methods=["POST"])
def spin():
    data = load_data()
    if not data["items"]:
        return jsonify({"error": "No items left"}), 400
    selected = random.choice(data["items"])
    data["items"].remove(selected)
    data["history"].append(selected)
    save_data(data)
    return jsonify({"result": selected})

@app.route("/api/win", methods=["POST"])
def save_win():
    data = request.get_json()
    item = data.get("item")
    invoice = data.get("invoice", "UNKNOWN")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([invoice, item, timestamp])

    return jsonify({"status": "success", "invoice": invoice, "item": item})

@app.route("/api/history")
def history():
    data = load_data()
    return jsonify(data["history"])

@app.route("/api/history/by-date", methods=["GET"])
def history_by_date():
    date_str = request.args.get("date")
    if not date_str:
        return jsonify([])

    results = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header if any
            for row in reader:
                if len(row) == 3 and row[2].startswith(date_str):
                    results.append({"invoice": row[0], "prize": row[1], "timestamp": row[2]})
    return jsonify(results)

@app.route("/api/export")
def export_csv():
    if not os.path.exists(CSV_FILE):
        return jsonify({"error": "No CSV file found"}), 404

    return send_file(
        CSV_FILE,
        mimetype='text/csv',
        as_attachment=True,
        download_name='lucky_draw_settlement.csv'
    )

@app.route("/api/clear", methods=["POST"])
def clear_csv():
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Invoice", "Prize", "Timestamp"])
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(debug=True)
