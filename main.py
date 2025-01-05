import urequests as requests
import ujson as json
import utime as time
from machine import RTC, ADC, Pin
import gc
import network
import dht

rtc = RTC()

# Constant
SITE_ID = 'KMac23a1e6aa8b'  # กำหนด Site ID
DEVICE_ID = 2  # กำหนด Device ID
BEARIOT_IP = '172.20.10.2'  # กำหนด Beariot IP
BEARIOT_PORT = 3300  # กำหนด PORT
API_ENDPOINT = f'http://{BEARIOT_IP}:{BEARIOT_PORT}/api/interfaces/update'  # กำหนด Endpoint ที่จะส่งข้อมูล

SSID = 'babydev'  # กำหนด SSID Wifi
PASSWORD = 'weangkom'  # กำหนด Password Wifi
MAX_WIFI_RETRIES = 10  # กำหนดจำนวนครั้งสูงสุดในการทดลองเชื่อมต่อ Wi-Fi

# เชื่อมต่อ WIFI
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    retry_count = 0
    while retry_count < MAX_WIFI_RETRIES:
        try:
            if not wlan.isconnected():
                print(f"Connecting to Wi-Fi... (Retry {retry_count+1})")
                wlan.connect(ssid, password)
                
                for _ in range(10):  # Check connection status for 10 seconds
                    if wlan.isconnected():
                        print("Connected to Wi-Fi:", wlan.ifconfig())
                        return True  # Return True when connected
                    time.sleep(1)
                
                print(f"Retrying Wi-Fi connection... (Attempt {retry_count+1})")
            else:
                print("Already connected to Wi-Fi:", wlan.ifconfig())
                return True  # Return True if already connected
            
        except OSError as e:
            print(f"Wi-Fi connection error: {e}")
            wlan.active(False)  # Disable the Wi-Fi interface
            time.sleep(1)  # Wait 1 second before retrying
            wlan.active(True)  # Re-enable the Wi-Fi interface
        
        retry_count += 1
        time.sleep(5)  # Wait 5 seconds before retrying
    
    print("Failed to connect to Wi-Fi after retries.")
    return False  # Return False if unable to connect after retries

# ตรวจสอบการเชื่อมต่อ WIFI และเชื่อมต่อใหม่ถ้าหลุด
def ensure_wifi_connected(ssid, password):
    wlan = network.WLAN(network.STA_IF)

    if not wlan.isconnected():
        print("Wi-Fi disconnected, reconnecting...")
        wlan.active(False)
        time.sleep(2)
        wlan.active(True)
        return connect_wifi(ssid, password)

# อ่านค่าอุณหภูมิ
def readDht22():
    dht_sensor = dht.DHT22(machine.Pin(15))
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()
    return {"temperature":temperature,"humidity":humidity}      


# สร้าง Payload เตรียมส่งข้อมูล
def generate_payload(temp, humid):
    current_time = rtc.datetime()
    iso_format = '{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:06d}+00:00'.format(
        current_time[0], current_time[1], current_time[2],
        current_time[4], current_time[5], current_time[6], current_time[7])
    #print(iso_format)

    return {
        "siteID": SITE_ID,
        "deviceID": DEVICE_ID,
        "date": iso_format,
        "offset": -420, 
        "connection": "REST",
        "tagObj": [{
            "status": True,
            "label": "temperature_restApi",
            "value": temp,
            "record": True,
            "update": "All",
        },
        {
            "status": True,
            "label": "humidity_restApi",
            "value": humid,
            "record": True,
            "update": "All",
        }]
    }

# ส่งข้อมูลด้วย RestAPI
def send_data(payload):
    try:
        response = requests.post(API_ENDPOINT, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        response.close()
        
        if response.status_code == 200:
            print(f"Data sent successfully: Temp : {payload['tagObj'][0]['value']} Humid : {payload['tagObj'][1]['value']}")
        else:
            print(f"Failed to send data. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

# ฟังก์ชั่นหลัก
def main():
    print("Starting BeaRiOt REST API Test")
    print(f"Sending data to: {API_ENDPOINT}")
    
    if not connect_wifi(SSID, PASSWORD):
        print("Initial Wi-Fi connection failed. Exiting...")
        return

    try:
        while True:
            ensure_wifi_connected(SSID, PASSWORD)
            dht22 = readDht22()
            payload = generate_payload(dht22["temperature"],dht22["humidity"])
            send_data(payload)
            gc.collect()
            time.sleep(1.1)
    except KeyboardInterrupt:
        print("Test stopped by user")

main()


