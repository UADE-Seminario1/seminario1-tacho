#! /usr/bin/python3
import sys
import time
from collections import deque
import requests


EMULATE_HX711 = False
referenceUnit = 1
sample_size = 20
API_URL = "http://glacial-garden-26787.herokuapp.com/api"
BIN_ID = "9903a7f1-cb25-4458-ab3a-d1638611eeda"
WAITING_TIME = 90 #in seconds


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
        #print(f"{r.status_code}: {url}")
        if r.status_code == requests.codes.ok:
            r = requests.get(url)
            conn = r.json()['data']
            break

    return conn


def accept_connection(connection_id, weight):
    url = f"{API_URL}/bins/connections/{connection_id}/accept"
    
    conn = None
    r = requests.patch(url, data={'initial_weight': weight})
    #print(f"{r.status_code}: {url}")
    if r.status_code == requests.codes.ok:
        conn = r.json()['data']
    
    return conn


def end_connection(connection_id, weight):
    url = f"{API_URL}/bins/connections/{connection_id}/end"

    conn = None
    r = requests.patch(url, data={'final_weight': weight})
    #print(f"{r.status_code}: {url}")
    if r.status_code == requests.codes.ok:
        conn = r.json()['data']

    return conn


def test():
    try:
        hx = setup_hx711()
        weight_range = capture_weight(hx)
        print(weight_range)
        
        print("esperando nuevas conexiones usuario-tacho...")
        new_conn = get_new_connection()
        print(new_conn)
        connection_id = new_conn['id']
        
        weight_range = capture_weight(hx)
        conn = accept_connection(connection_id, weight_range[1])
        print(conn)
        
        print("esperando que el usuario deposite los residuos...")
        time.sleep(WAITING_TIME)

        weight_range = capture_weight(hx)
        print(weight_range)
        
        print("finalizando la conexion usuario-tacho...")
        conn = end_connection(connection_id, weight_range[1])
        print(conn)
    except (KeyboardInterrupt, SystemExit):
        cleanAndExit()


def main_loop():
    hx = setup_hx711()
   
    def _reset_queue():
        return deque([], maxlen=sample_size)
    
    def _avg_weights(sample):
        return sum(sample) / len(sample)

    sample = _reset_queue()
    connection_id = None
    bin_state = "receiving"
    

    while True:
        try:
            weight = hx.get_weight(5)
            sample.append(weight)
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)
            
            if bin_state == "receiving":
                print("esperando nuevas conexiones usuario-tacho...")
                new_conn = get_new_connection()
                connection_id = new_conn['id']
                print(f"conexion '{connection_id}' recibida")
                bin_state = "accepting"
                continue
            
            if bin_state == "accepting" and len(sample) == sample_size:
                weight_avg = _avg_weights(sample)
                print(f"aceptando la conexion '{connection_id}' weight={weight_avg}...")
                accept_connection(connection_id, weight_avg)
                print("conexion usuario-tacho aceptada")
                bin_state = "throwing"
                continue

            if bin_state == "throwing":
                print("esperando que el usuario deposite los residuos...")
                time.sleep(WAITING_TIME)
                sample = _reset_queue()
                bin_state = "ending"
                continue

            if bin_state == "ending" and len(sample) == sample_size:
                weight_avg = _avg_weights(sample)
                print(f"finalizando la conexion {connection_id} weight={weight_avg}...")
                end_connection(connection_id, weight_range[1])
                print("conexion usuario-tacho finalizada")
                bin_state = "receiving"
                continue
        except (KeyboardInterrupt, SystemExit):
            cleanAndExit()
        

            
if __name__ == "__main__":
    main_loop()

