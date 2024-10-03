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
BEARIOT_IP = '172.20.10.4'  # กำหนด Beariot IP
BEARIOT_PORT = 3300  # กำหนด PORT
API_ENDPOINT = f'http://{BEARIOT_IP}:{BEARIOT_PORT}/api/interfaces/update'  # กำหนด Endpoint ที่จะส่งข้อมูล

SSID = 'bi2sb2te3'  # กำหนด SSID Wifi
PASSWORD = '94dda6f6'  # กำหนด Password Wifi

# เชื่อมต่อ WIFI
def connect_wifi(ssid, password, max_retries=10):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    # พยายามเชื่อมต่อ Wi-Fi
    retry_count = 0
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(ssid, password)

    # ลองเชื่อมต่อหลายครั้งจนสำเร็จหรือเกินจำนวนครั้งที่กำหนด
    while not wlan.isconnected() and retry_count < max_retries:
        time.sleep(2)
        retry_count += 1
        print(f"Waiting for connection... ({retry_count}/{max_retries})")
    
    if wlan.isconnected():
        print("Connected to Wi-Fi:", wlan.ifconfig())
        return True
    else:
        print("Failed to connect to Wi-Fi.")
        return False

# ตรวจสอบการเชื่อมต่อ WIFI และเชื่อมต่อใหม่ถ้าหลุด
def ensure_wifi_connected(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    
    if not wlan.isconnected():
        print("Wi-Fi disconnected, reconnecting...")
        wlan.active(False)
        time.sleep(2)
        wlan.active(True)
        
        # ลองเชื่อมต่อใหม่
        success = connect_wifi(ssid, password)
        
        if not success:
            print("Wi-Fi reconnect failed. Retrying after delay...")
            time.sleep(5)  # รอซักครู่ก่อนลองอีกครั้ง
            connect_wifi(ssid, password)

# อ่านค่าอุณหภูมิ
def read_temperature():
    raw_value = adc.read_u16()
    conversion_factor = 3.3 / 65535
    convert_voltage = raw_value * conversion_factor
    voltage = convert_voltage * 100
    temperature_c = voltage
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
    
    if not connect_wifi(SSID, PASSWORD):
        print("Initial Wi-Fi connection failed. Exiting...")
        return

    try:
        while True:
            ensure_wifi_connected(SSID, PASSWORD)  # ตรวจสอบการเชื่อมต่อ Wi-Fi ในทุกลูป
            value = read_temperature()
            payload = generate_payload(value)
            send_data(payload)
            gc.collect()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Test stopped by user")

if __name__ == "__main__":
    main()
