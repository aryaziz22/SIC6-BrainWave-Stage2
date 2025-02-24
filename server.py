from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import traceback  # Untuk menangkap error lebih rinci

app = Flask(__name__)

# MongoDB Atlas Connection
MONGO_URI = "mongodb+srv://dbRenaldiEndrawan:BrainWave123@cluster0.b6oba.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGO_URI)
    db = client.get_database("dbSIC_BrainWave")
    collection = db.get_collection("data_sensor")
    print("✅ MongoDB Connected Successfully!")
except Exception as e:
    print("❌ Error connecting to MongoDB:", str(e))

@app.route('/data', methods=['POST'])
def receive_data():
    """Receive data from ESP32 and store it in MongoDB"""
    try:
        raw_data = request.data.decode("utf-8")  # Debugging: tampilkan data mentah
        print(f"📥 Raw Data Received: '{raw_data}'")  # Tambahkan tanda kutip untuk cek apakah kosong

        if not raw_data.strip():  # Jika kosong, kembalikan error
            return jsonify({"status": "error", "message": "Received empty request body"}), 400

        data = request.get_json(silent=True)  # Gunakan silent=True agar tidak crash
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON format"}), 400

        print("📩 Parsed JSON:", data)

        # Validasi apakah JSON memiliki field yang diperlukan
        required_fields = ["temp", "hum", "dist"]
        for field in required_fields:
            if field not in data:
                return jsonify({"status": "error", "message": f"Missing field: {field}"}), 400

            if not isinstance(data[field], (int, float)):
                return jsonify({"status": "error", "message": f"Invalid data type for {field}"}), 400

        data["timestamp"] = datetime.utcnow()
        collection.insert_one(data)
        print(f"✅ Data Inserted: {data}")

        return jsonify({"status": "success", "message": "Data stored successfully"}), 201

    except Exception as e:
        error_message = str(e)
        traceback_message = traceback.format_exc()
        print("❌ Error Occurred:\n", traceback_message)
        return jsonify({"status": "error", "message": error_message, "trace": traceback_message}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
