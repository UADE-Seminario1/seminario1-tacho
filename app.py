#! /usr/bin/python3
import sys
import time
import requests


EMULATE_HX711 = False
referenceUnit = 1
sample_size = 20
API_URL = "http://glacial-garden-26787.herokuapp.com/api"
BIN_ID = "9903a7f1-cb25-4458-ab3a-d1638611eeda"


if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711
else:
    from emulated_hx711 import HX711


def cleanAndExit():
    print("Cleaning...")

    if not EMULATE_HX711:
        GPIO.cleanup()

    print("Bye!")
    sys.exit()


def capture_weight(hx):
    values = []
    
    n = 0
    while n <= sample_size:
        val = hx.get_weight(5)
        print(val)
        if val <= 0:
            continue
        values.append(val)
        hx.power_down()
        hx.power_up()
        time.sleep(0.1)
        n += 1

    weight = sum(values) / len(values)

    return (min(values), weight, max(values))


def setup_hx711():
    hx = HX711(5, 6)
    hx.set_reading_format("MSB", "MSB")
    hx.set_reference_unit(21)
    hx.reset()
    hx.tare()

    return hx


def get_new_connection():
    url = f"{API_URL}/bins/{BIN_ID}/connections/requested"

    conn = None
    while True:
        r = requests.head(url)
        print(r.status_code, ":", url)
        if r.status_code == requests.codes.ok:
            r = requests.get(url)
            conn = r.json()
            break

    return conn


def main():
    hx = setup_hx711()
    weight_range = capture_weight(hx)
    print(weight_range) 
    conn = get_new_connection()
    print(conn)

    weight_range = capture_weight(hx)
    print(weight_range)

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()

