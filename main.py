import network
import time
from microdot import Microdot, Response
import machine
import dht
from config import *

# ----------------------------
# Wi-Fi setup
# ----------------------------
is_wlan_connected = False
wlan_ip = "not set"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def wlan_connect(ssid, pwd):
    wlan.disconnect()
    wlan.connect(ssid, pwd)
    wait = 30
    while wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        wait -= 1
        time.sleep(1)

def wlan_connected():
    return wlan.status() == 3

def wlan_init():
    global is_wlan_connected
    global wlan_ip

    wlan_ssid = config["wlan_ssid"]
    wlan_pwd = config["wlan_pwd"]

    wlan_connect(wlan_ssid, wlan_pwd)

    if not wlan_connected():
        wlan_ssid = config["wlan_ssid_fallback"]
        wlan_pwd = config["wlan_pwd_fallback"]
        wlan_connect(wlan_ssid, wlan_pwd)

    if not wlan_connected():
        is_wlan_connected = False
    else:
        wlan_ip = wlan.ifconfig()[0]
        is_wlan_connected = True

# ----------------------------
# Microdot setup
# ----------------------------
Response.default_content_type = 'text/html'
app = Microdot()

# ----------------------------
# Sensors
# ----------------------------
soil = machine.ADC(machine.Pin(27))      # Soil moisture sensor
ldr = machine.ADC(machine.Pin(28))       # Light sensor
dht_sensor = dht.DHT11(machine.Pin(15))  # Temperature & Humidity

# ----------------------------
# Optimal ranges
# ----------------------------
OPT = {
    "soil_moisture": {"min": 30000, "max": 45000},
    "ldr": {"min": 20000, "max": 50000},
    "temperature": {"min": 20, "max": 28},
    "humidity": {"min": 50, "max": 80}
}

def get_status(readings):
    messages = []

    if readings["soil_moisture"] != "N/A":
        if readings["soil_moisture"] < OPT["soil_moisture"]["min"]:
            messages.append("Soil too dry")
        elif readings["soil_moisture"] > OPT["soil_moisture"]["max"]:
            messages.append("Soil too wet")

    if readings["ldr"] != "N/A":
        if readings["ldr"] < OPT["ldr"]["min"]:
            messages.append("Not enough light")
        elif readings["ldr"] > OPT["ldr"]["max"]:
            messages.append("Too much light")

    if readings["temperature"] != "N/A":
        if readings["temperature"] < OPT["temperature"]["min"]:
            messages.append("Temperature too low")
        elif readings["temperature"] > OPT["temperature"]["max"]:
            messages.append("Temperature too high")

    if readings["humidity"] != "N/A":
        if readings["humidity"] < OPT["humidity"]["min"]:
            messages.append("Humidity too low")
        elif readings["humidity"] > OPT["humidity"]["max"]:
            messages.append("Humidity too high")

    return messages if messages else ["All good"]

# ----------------------------
# Webpage route
# ----------------------------
@app.route('/')
def index(request):
    try:
        # Read sensors
        soil_val = soil.read_u16()
        ldr_val = ldr.read_u16()

        # DHT read in try/except to prevent ETIMEDOUT
        try:
            dht_sensor.measure()
            temp_val = dht_sensor.temperature()
            hum_val = dht_sensor.humidity()
        except Exception:
            temp_val = "N/A"
            hum_val = "N/A"

        readings = {
            "soil_moisture": soil_val,
            "ldr": ldr_val,
            "temperature": temp_val,
            "humidity": hum_val
        }
        status = ", ".join(get_status(readings))

        html = f"""
        <html>
        <head>
            <title>Plant Monitor</title>
            <meta http-equiv="refresh" content="5">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f4f4f4;
                    text-align: center;
                    padding: 20px;
                }}
                .card {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px auto;
                    box-shadow: 0px 0px 10px rgba(0,0,0,0.1);
                    max-width: 400px;
                }}
                h1 {{ color: #2c3e50; }}
                p {{ font-size: 18px; }}
                .status {{ font-weight: bold; color: #27ae60; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🌱 Plant Monitor</h1>
                <p><b>Soil Moisture:</b> {soil_val}</p>
                <p><b>Light:</b> {ldr_val}</p>
                <p><b>Temperature:</b> {temp_val}</p>
                <p><b>Humidity:</b> {hum_val}</p>
                <p class="status">Status: {status}</p>
                <small>Auto-refreshes every 5s</small>
            </div>
        </body>
        </html>
        """
        return html

    except Exception as e:
        return f"<html><body><h1>Error: {str(e)}</h1></body></html>"

# ----------------------------
# Connect Wi-Fi and run server
# ----------------------------
while not wlan_connected():
    time.sleep(2)
    wlan_init()

print(f"✅ Connected! Open in browser: http://{wlan.ifconfig()[0]}")
app.run(host="0.0.0.0", port=80)

