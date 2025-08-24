import network
import time
from microdot import Microdot, Response
import machine
import dht
from config import *

# ----------------------------
# Wi-Fi setup
# ----------------------------
# WLAN connected status flag
is_wlan_connected = False
wlan_ip = "not set"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

def wlan_connect(ssid, pwd):
    wlan.disconnect()
    wlan.connect(ssid, pwd)

    # Wait for connect or fail
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

    # Get preferred WAN SSID and password from config file
    wlan_ssid = config["wlan_ssid"]
    wlan_pwd = config["wlan_pwd"]

    # Connect to WLAN
    wlan_connect(wlan_ssid, wlan_pwd)

    # If WLAN did not connect then try fallback SSID and password
    if not wlan_connected():
        wlan_ssid = config["wlan_ssid_fallback"]
        wlan_pwd = config["wlan_pwd_fallback"]
        wlan_connect(wlan_ssid, wlan_pwd)

    # Handle connection error
    if not wlan_connected():
        is_wlan_connected = False
    else:
        wlan_ip = wlan.ifconfig()[0]
        is_wlan_connected = True

# ----------------------------
# Microdot setup
# ----------------------------
Response.default_content_type = 'application/json'
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

    if readings["soil_moisture"] < OPT["soil_moisture"]["min"]:
        messages.append("Soil too dry")
    elif readings["soil_moisture"] > OPT["soil_moisture"]["max"]:
        messages.append("Soil too wet")

    if readings["ldr"] < OPT["ldr"]["min"]:
        messages.append("Not enough light")
    elif readings["ldr"] > OPT["ldr"]["max"]:
        messages.append("Too much light")

    if readings["temperature"] < OPT["temperature"]["min"]:
        messages.append("Temperature too low")
    elif readings["temperature"] > OPT["temperature"]["max"]:
        messages.append("Temperature too high")

    if readings["humidity"] < OPT["humidity"]["min"]:
        messages.append("Humidity too low")
    elif readings["humidity"] > OPT["humidity"]["max"]:
        messages.append("Humidity too high")

    return messages if messages else ["All good"]

# ----------------------------
# Microdot route
# ----------------------------
#@app.route('/')
#def index(request):
#    try:
#        soil_val = soil.read_u16()
#        ldr_val = ldr.read_u16()
#        dht_sensor.measure()
#        temp_val = dht_sensor.temperature()
#        hum_val = dht_sensor.humidity()

#        readings = {
#            "soil_moisture": soil_val,
#            "ldr": ldr_val,
#            "temperature": temp_val,
#            "humidity": hum_val
#        }
#        status = ", ".join(get_status(readings))
#
#        return {"readings": readings, "status": status}

#    except Exception as e:
#        return {"error": str(e)}

# ----------------------------
# Run server
# ----------------------------
#app.run(host="0.0.0.0", port=80)

while not wlan_connected():
        # Sleep for two seconds
        time.sleep(2)

        # Initialise WLAN
        wlan_init()
        continue
    
while True:
    try:
       soil_val = soil.read_u16()
       ldr_val = ldr.read_u16()
       dht_sensor.measure()
       temp_val = dht_sensor.temperature()
       hum_val = dht_sensor.humidity()

       readings = {
           "soil_moisture": soil_val,
           "ldr": ldr_val,
           "temperature": temp_val,
           "humidity": hum_val
       }
       status = ", ".join(get_status(readings))

       print(f"readings: {readings}, status: {status}")

    except Exception as e:
       print(f"error: {str(e)}")


