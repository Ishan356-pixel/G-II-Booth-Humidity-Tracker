import network
import ubinascii
## Subscription Label: diddy-esp32/telemetry
# 1. Activate the Wi-Fi Station (STA) interface
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# 2. Retrieve the raw MAC address bytes
mac_bytes = wlan.config('mac')

# 3. Format it into standard colon-separated hex format
# Option A: Using list comprehension (Universal)
mac_address = ':'.join(['%02x' % b for b in mac_bytes])

# Option B: Using ubinascii (Alternative)
# mac_address = ubinascii.hexlify(mac_bytes, ':').decode()

print("ESP32 MAC Address:", mac_address.upper())
###################################################
import network
import time

ssid = "umd-iot"
password = "vwFNgKFqKU4C"   # your device password

wifi = network.WLAN(network.STA_IF)
wifi.active(True)

print("Connecting to UMD-IoT...")
wifi.connect(ssid, password)

# Wait for connection
for _ in range(20):
    if wifi.isconnected():
        break
    time.sleep(1)

if wifi.isconnected():
    print("Connected!")
    print("IP address:", wifi.ifconfig()[0])
else:
    print("Failed to connect.")
############################################

import network, time, machine, ubinascii, ujson, dht
from umqtt.simple import MQTTClient
from machine import Pin
sensor = dht.DHT22(Pin(15))

SSID = "umd-iot"
PASSWORD = "vwFNgKFqKU4C"

BROKER = "broker.hivemq.com"
PORT = 1883

# Telemetry: device -> broker
TELEMETRY_TOPIC = b"diddy-esp32/telemetry"
# Subscription: broker -> device
SUBSCRIPTION_TOPIC = b"diddy-esp32/commands"

TELEMETRY_INTERVAL_MS = 5000

def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("MAC:", ubinascii.hexlify(wlan.config("mac"), ":").decode())
        wlan.connect(SSID, PASSWORD)
        t = 0
        while not wlan.isconnected() and t < 30:
            time.sleep(1); t += 1
    if not wlan.isconnected():
        raise RuntimeError("WiFi failed, status=%s" % wlan.status())
    print("WiFi OK:", wlan.ifconfig())

def read_sensor():
    try:
        sensor.measure()
        return {"temp_c": sensor.temperature(), "humidity": sensor.humidity()}
    except OSError as e:
        print("Sensor read failed:", e)
        return None

def on_message(topic, msg):
    # Handles anything arriving on the subscription topic
    print("Received:", topic, msg)
    try:
        cmd = ujson.loads(msg)
        # Example: {"led": 1}
        if "led" in cmd:
            machine.Pin(2, machine.Pin.OUT).value(cmd["led"])
    except ValueError:
        print("Not JSON:", msg)

def mqtt_connect():
    client_id = b"esp32-" + ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, BROKER, port=PORT, keepalive=60)
    client.set_callback(on_message)
    client.connect()
    client.subscribe(SUBSCRIPTION_TOPIC)
    print("MQTT connected, subscribed to", SUBSCRIPTION_TOPIC)
    return client

def publish_telemetry(client):
    payload = ujson.dumps(read_sensor())
    client.publish(TELEMETRY_TOPIC, payload)
    print("Telemetry sent:", payload)

wifi_connect()
client = mqtt_connect()
last = time.ticks_ms()

while True:
    try:
        client.check_msg()
        if time.ticks_diff(time.ticks_ms(), last) > TELEMETRY_INTERVAL_MS:
            publish_telemetry(client)
            last = time.ticks_ms()
        time.sleep(0.1)
    except OSError as e:
        print("Connection lost:", e)
        time.sleep(5)
        try:
            wifi_connect()
            client = mqtt_connect()
        except OSError as e2:
            print("Reconnect failed:", e2)