from flask import Flask, request, jsonify
from datetime import datetime
import threading

app = Flask(__name__)

# LED durumları ve diğer veriler
led_status = {"LED1": 0, "LED2": 0, "LED3": 0}
led_durations = {"LED1": 0, "LED2": 0, "LED3": 0}
led_last_on_time = {"LED1": None, "LED2": None, "LED3": None}
sensor_data_log = []  # Sensör verilerinin loglanması için liste
previous_data = None

@app.route('/data', methods=['POST'])
def receive_sensor_data():
    """
    ESP32'nin gönderdiği veriyi alır ve işler.
    """
    global led_status, led_durations, led_last_on_time, sensor_data_log, previous_data
    
    # JSON verisini al
    data = request.get_json()
    print(data)
    if not data:
        return jsonify({"error": "JSON formatında veri bekleniyor"}), 400
    led = list(data.keys())[0]
    # Veriyi işleme
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sensor_data = {
        "timestamp": timestamp,
        led : list(data.values())[0],
    }

    sensor_data_log.append(sensor_data)
    return jsonify({"message": "Data received successfully"}), 200

@app.route('/data', methods=['GET'])
def get_sensor_data():
    """
    Bir istemci talep ettiğinde sensör verilerini döndürür.
    """
    return jsonify(sensor_data_log), 200

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """
    LED yanma sürelerini ve diğer metrikleri döndürür.
    """
    metrics = {
        "led_durations": led_durations,
        "total_entries": len(sensor_data_log),
    }
    return jsonify(metrics), 200

if __name__ == '__main__':
    # Sunucuyu başlat
    app.run(host="0.0.0.0", port=5000, debug=True)
