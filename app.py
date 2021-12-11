#! /usr/bin/python3
import sys


EMULATE_HX711 = False
referenceUnit = 1
sample_size = 20


if not EMULATE_HX711:
    import RPi.GPIO as GPIO
    from hx711 import HX711

    pass
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

    for _ in range(sample_size):
        val = hx.get_weight(5)
        values.append(val)

    return values


def setup_hx711():
    hx = HX711(5, 6)
    hx.set_reading_format("MSB", "MSB")
    hx.set_reference_unit(referenceUnit)
    hx.reset()
    hx.tare()

    return hx


def main():
    hx = setup_hx711()
    print(capture_weight(hx))


if __name__ == "__main__":
    main()
