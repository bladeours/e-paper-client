import utime
import network
import urequests
import driver
from machine import Pin, Timer, ADC


def read_conf_to_dict(filename=".config"):
    config = {}
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip()
    except OSError:
        print(f"File {filename} not found!")
    return config


led = Pin("LED", Pin.OUT)
counter = 0
refresh_period_min = int(read_conf_to_dict()["refresh_period_min"])
refresh_period_sec = 60 * refresh_period_min
blink = False



def connect_wifi():
    conf = read_conf_to_dict()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to network...")
        wlan.connect(conf.get("ssid"), conf.get("password"))
        while not wlan.isconnected():
            utime.sleep_ms(500)
    print("Connected, IP:", wlan.ifconfig()[0])
    return wlan


def download_calendar_image():
    url = read_conf_to_dict().get("url")
    max_retries = int(read_conf_to_dict().get("max_retries"))
    delay = int(read_conf_to_dict().get("delay_retry_s"))
    print(f"url: {url}")

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Downloading bitmap... (attempt {attempt}/{max_retries})")
            response = urequests.get(url)
            data = response.content
            response.close()
            print("Download complete, bytes:", len(data))
            return data

        except Exception as e:
            print("Error downloading image:", e)
            if attempt < max_retries:
                print(f"Retrying in {delay} seconds...")
                utime.sleep_ms(delay * 1000)

    print("Failed to download image after", max_retries, "attempts")
    return None


def load_epd_data(epd, data):
    # Split black and red channel
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
    global blink
    blink = True
    wlan = connect_wifi()
    data = download_calendar_image()
    if data is None:
        wlan.disconnect()
        print("No data!")
        return
    load_epd_data(epd, data)
    print("data loaded")
    blink = False
    led.off()
    epd.init()
    epd.display()
    print("Display updated")
    wlan.disconnect()
    epd.sleep()

def toggle_led(timer):
    if blink:
        led.toggle()

def refresh(timer):
    global counter
    if counter < refresh_period_sec:
        counter += 1
        #if counter % 10 == 0:
        #    print("Refresh counter: ", counter)


if __name__ == "__main__":
    toggle_led_timer = Timer() # type: ignore
    toggle_led_timer.init(period=500, mode=Timer.PERIODIC, callback=toggle_led)

    refresh_timer = Timer() # type: ignore
    refresh_timer.init(period=1000, mode=Timer.PERIODIC, callback=refresh)
    epd = driver.EPD_7in5_B()

    btn1 = Pin("GP2", Pin.IN, Pin.PULL_UP)
    btn2 = Pin("GP3", Pin.IN, Pin.PULL_UP)

    print(f"Press Button 1 or Button 2 to refresh display or wait {refresh_period_sec} seconds.")
    led.on()
    utime.sleep_ms(2000)
    led.off()

    while True:
        if btn1.value() == 0 or btn2.value() == 0:
            print("Button pressed -> updating display")
            counter = 0
            update_display(epd)
            counter = 0
            utime.sleep_ms(500)
            print(f"done updating, reset counter to {counter}")
        if counter == refresh_period_sec:
            print(f"counter == {refresh_period_sec} -> updating display")
            update_display(epd)
            counter = 0
            print(f"done updating, reset counter to {counter}")

        full_battery = 4.2                  # these are our reference voltages for a full/empty battery, in volts
        empty_battery = 2.75

        vsys = ADC(29)
        conversion_factor = 3 * 3.3 / 65535  # mnożnik 3 bierze pod uwagę dzielnik na PIM557
        voltage = vsys.read_u16() * conversion_factor

        percentage = (voltage - empty_battery) / (full_battery - empty_battery) * 100
        if percentage > 100:
            percentage = 100
        elif percentage < 0:
            percentage = 0

        #print("Battery voltage:", voltage)
        #print("Battery percentage:", percentage, "%")

        utime.sleep_ms(500)