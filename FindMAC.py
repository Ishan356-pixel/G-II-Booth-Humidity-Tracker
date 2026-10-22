import network
import ubinascii
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