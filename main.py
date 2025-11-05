import utime
import network
import urequests
import driver
from machine import deepsleep

LOG_FILE = "log.txt"
MAX_LOG_SIZE = 1000 * 1024  # 1000 KB

def log(msg, level="INFO"):
    ts = utime.localtime()
    timestamp = f"{ts[0]:04d}-{ts[1]:02d}-{ts[2]:02d} {ts[3]:02d}:{ts[4]:02d}:{ts[5]:02d}"
    line = f"[{timestamp}] [{level}] {msg}\n"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except OSError:
        with open(LOG_FILE, "w") as f:
            f.write(line)
    try:
        import os
        if os.stat(LOG_FILE)[6] > MAX_LOG_SIZE:
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()[-200:]
            with open(LOG_FILE, "w") as f:
                f.writelines(lines)
            log("Log rotated (too large)", "DEBUG")
    except Exception as e:
        print("Logging error:", e)

def read_conf_to_dict(filename=".config"):
    cfg = {}
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    cfg[key.strip()] = value.strip()
    except OSError:
        log(f"File {filename} not found!", "ERROR")
    return cfg

conf = read_conf_to_dict()
refresh_period_min = int(conf.get("refresh_period_min", "60"))
refresh_period_ms = refresh_period_min * 60 * 1000

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        log("Connecting WiFi…")
        wlan.connect(conf.get("ssid"), conf.get("password"))
        while not wlan.isconnected():
            utime.sleep_ms(500)
    ip = wlan.ifconfig()[0]
    log(f"Connected WiFi: {ip}")
    return wlan

def download_calendar_image():
    url = conf.get("url")
    retries = int(conf.get("max_retries", "3"))
    delay = int(conf.get("delay_retry_s", "5"))
    timeout = int(conf.get("timeout_s", "10"))
    for attempt in range(1, retries + 1):
        try:
            log(f"Download attempt {attempt}/{retries}")
            r = urequests.get(url, timeout=timeout)
            data = r.content
            r.close()
            log(f"Downloaded {len(data)} bytes")
            if len(data) != 96000:
                raise Exception(f"number of bytes should be 96000 but is {len(data)}")
            return data
        except Exception as e:
            log(f"Download error: {e}", "ERROR")
            if attempt < retries:
                utime.sleep(delay)
    return None

def load_epd_data(epd, data):
    total_bytes = len(data) // 2
    black_data = data[:total_bytes]
    red_data = data[total_bytes:]
    i = 0
    for y in range(driver.EPD_HEIGHT):
        for x in range(driver.EPD_WIDTH):
            byte_index = i // 8
            bit_index = 7 - (i % 8)
            black_bit = (black_data[byte_index] >> bit_index) & 1
            red_bit = (red_data[byte_index] >> bit_index) & 1
            epd.imageblack.pixel(x, y, 0x00 if black_bit else 0xff)
            epd.imagered.pixel(x, y, 0xff if red_bit else 0x00)
            i += 1

def update_display(epd):
    wlan = connect_wifi()
    data = download_calendar_image()
    wlan.disconnect()
    if data is None:
        log("No data, skipping update", "WARNING")
        return
    epd.init()
    log("loading data to driver")
    load_epd_data(epd, data)
    epd.display()
    log("Display updated")
    epd.sleep()

if __name__ == "__main__":
    log("Starting update cycle")
    epd = driver.EPD_7in5_B()
    update_display(epd)
    log("Waiting 60 seconds before sleep")
    utime.sleep(60)
    log(f"Deep sleep for {refresh_period_min} min")
    deepsleep(refresh_period_ms)
