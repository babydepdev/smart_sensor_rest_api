import urequests as requests
import ujson as json
import utime as time
from machine import RTC, ADC
import gc
import network

adc = ADC(26)
rtc = RTC()

# กำหนดค่า
SITE_ID = 'KMe45f01d94cbf'  # กำหนด Site ID
DEVICE_ID = 2  # กำหนด Device ID
BEARIOT_IP = '172.20.10.2'  # กำหนด Beariot IP
BEARIOT_PORT = 3300  # กำหนด PORT
API_ENDPOINT = f'http://{BEARIOT_IP}:{BEARIOT_PORT}/api/interfaces/update' #กำหนด Endpoint ที่จะส่งข้อมูล


SSID = 'bi2sb2te3' # กำหนด SSID Wifi
PASSWORD = '94dda6f6' # กำหนด Password Wifi


# เชื่อมต่อ WIFI
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    while not wlan.isconnected():
        time.sleep(1)
        print("Connecting to Wi-Fi...")
    print("Connected to Wi-Fi:", wlan.ifconfig())

#อ่านค่าอุณหภูมิ
def read_temperature():
    raw_value = adc.read_u16()
    
    voltage = (raw_value / 65535.0) * 3.3
    
    temperature_c = voltage / 0.01
    return temperature_c

# สร้าง Payload เตรียมส่งข้อมูล
def generate_payload(value):
    current_time = rtc.datetime()
    iso_format = '{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}.{:06d}+00:00'.format(
        current_time[0], current_time[1], current_time[2],
        current_time[4], current_time[5], current_time[6], current_time[7])
    print(iso_format)

    return {
        "siteID": SITE_ID,
        "deviceID": DEVICE_ID,
        "date": iso_format,
        "offset": -420, 
        "connection": "REST",
        "tagObj": [{
            "status": True,
            "label": "rest_api",
            "value": value,
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
            print(f"Data sent successfully: {payload['tagObj'][0]['value']}")
        else:
            print(f"Failed to send data. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

# ฟังก์ชั่นหลัก
def main():
    print("Starting BeaRiOt REST API Test")
    print(f"Sending data to: {API_ENDPOINT}")
    
    connect_wifi(SSID, PASSWORD)
    
    try:
        while True:
            value = read_temperature()
            payload = generate_payload(value)
            send_data(payload)
            gc.collect() 
            time.sleep(5) 
    except KeyboardInterrupt:
        print("Test stopped by user")

if __name__ == "__main__":
    main()