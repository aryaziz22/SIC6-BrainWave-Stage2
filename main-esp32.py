import urequests
import network
import time
import dht
import machine
import ujson
from machine import Pin, time_pulse_us

# WiFi credentials
WIFI_SSID = "Mas Reza"
WIFI_PASSWORD = "aaaaaaaa"

# API Server
SERVER_URL = "http://192.168.0.102:5000/data"  # Ganti dengan IP PC yang menjalankan Flask

# Sensor setup
DHT_PIN = Pin(15)
dht_sensor = dht.DHT11(DHT_PIN)

TRIG_PIN = Pin(2, Pin.OUT)
ECHO_PIN = Pin(4, Pin.IN)

def connect_wifi():
    """Connect to WiFi"""
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASSWORD)

    print("Connecting to WiFi", end="")
    timeout = 10
    while not wifi.isconnected() and timeout > 0:
        print(".", end="")
        time.sleep(1)
        timeout -= 1

    if wifi.isconnected():
        print("\n✅ WiFi Connected!")
        print("📡 IP Address:", wifi.ifconfig()[0])
    else:
        print("\n❌ WiFi connection failed. Rebooting...")
        machine.reset()

def read_ultrasonic():
    """Read distance from ultrasonic sensor"""
    TRIG_PIN.off()
    time.sleep_us(2)
    TRIG_PIN.on()
    time.sleep_us(10)
    TRIG_PIN.off()

    duration = time_pulse_us(ECHO_PIN, 1, 30000)
    if duration < 0:
        return None  # Jika gagal membaca

    dist = (duration * 0.0343) / 2
    return round(dist, 2)

def read_dht():
    """Read temperature & humidity from DHT11"""
    for _ in range(3):  # Coba membaca hingga 3 kali
        try:
            dht_sensor.measure()
            temp = float(dht_sensor.temperature())
            hum = float(dht_sensor.humidity())

            # Validasi data agar tidak ada karakter aneh
            if -40 <= temp <= 80 and 0 <= hum <= 100:
                return temp, hum
        except Exception as e:
            print("❌ Error reading DHT sensor:", e)
            time.sleep(1)

    return None, None  # Jika gagal membaca sensor

def send_http_data(temp, hum, dist):
    """Send sensor data to Flask server via HTTP"""
    if temp is None or hum is None or dist is None:
        print("⚠️ Invalid sensor data, skipping HTTP request...")
        return

    # Buat JSON dengan key yang benar
    payload = {
        "temp": round(temp, 2),  # Menggunakan kunci yang sesuai dengan yang diharapkan server
        "hum": round(hum, 2),
        "dist": round(dist, 2)
    }

    # Konversi JSON ke format string
    try:
        json_payload = ujson.dumps(payload)  # FIX encoding
    except Exception as e:
        print("❌ Error encoding JSON:", e)
        return

    headers = {"Content-Type": "application/json"}

    print(f"📤 Sending JSON: {json_payload}")

    for attempt in range(3):  # Retry jika gagal
        try:
            response = urequests.post(SERVER_URL, data=json_payload, headers=headers)
            response_text = response.text.strip()  # Bersihkan karakter aneh
            print(f"✅ Response: {response_text}")
            response.close()
            return
        except Exception as e:
            print(f"❌ Error sending data (Attempt {attempt + 1}/3):", e)
            time.sleep(2)

    print("❌ Failed to send data after 3 attempts.")

# Mulai eksekusi
connect_wifi()

while True:
    temp, hum = read_dht()
    dist = read_ultrasonic()

    print(f"🌡️ Temp: {temp}°C, 💧 Hum: {hum}%, 📏 Dist: {dist} cm")

    send_http_data(temp, hum, dist)

    time.sleep(10)