#!/usr/bin/env python3

import sys
import time
import pandas as pd
from pathlib import Path
import datetime


try:
    # Transitional fix for breaking change in LTR559
    from ltr559 import LTR559
    ltr559 = LTR559()
except ImportError:
    import ltr559

import logging

from bme280 import BME280
from pms5003 import PMS5003
from pms5003 import ReadTimeoutError as pmsReadTimeoutError

from enviroplus import gas

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S")

logging.info("""all-in-one.py - Displays readings from all of Enviro plus' sensors

Press Ctrl+C to exit!

""")

# BME280 temperature/pressure/humidity sensor
bme280 = BME280()

# PMS5003 particulate sensor
pms5003 = PMS5003()

class DataWriter:
    def __init__(self, path, buffer_size):
        self.path = Path(path)
        self.buffer_size = buffer_size
        self.buffer = []
        self.write_header = True

    def update(self, data):
        if len(self.buffer) == self.buffer_size:
            df = pd.DataFrame(self.buffer)
            with open(self.path, 'a') as f:
                df.to_csv(f, header=self.write_header, index=False)
                self.write_header = False
            self.buffer = []
        self.buffer.append(data)
            
writer = DataWriter("/home/rp/Projects/enviro_plus/enviroplus-python/examples/baseline_data.csv" ,  50)

def get_temperature():
    # unit = "°C"
    # cpu_temp = get_cpu_temperature()
    # Smooth out with some averaging to decrease jitter
    # cpu_temps = cpu_temps[1:] + [cpu_temp]
    # avg_cpu_temp = sum(cpu_temps) / float(len(cpu_temps))
    raw_temp = bme280.get_temperature()
    # data = raw_temp - ((avg_cpu_temp - raw_temp) / factor)
    return raw_temp

try:
    while True:

        temperature = get_temperature()
        pressure = bme280.get_pressure()
        humidity = bme280.get_humidity()
        lux = ltr559.get_lux()
        data = gas.read_all()
        ox_gas = data.oxidising / 1000
        red_gas = data.reducing / 1000
        nh3_gas = data.nh3 / 1000


        # variable = "pm1"
        try:
            pm = pms5003.read()
            pm1 = float(pm.pm_ug_per_m3(1.0))
            pm2p5 = float(pm.pm_ug_per_m3(2.5))
            pm10 = float(pm.pm_ug_per_m3(10))
        except pmsReadTimeoutError:
            logging.warning("Failed to read PMS5003")

        data = {
            "time": str(datetime.datetime.now()),
            "temperature (°C)": temperature,
            "pressure (hPA)": pressure,
            "humidity (%)": humidity,
            "light (lux)": lux,
            "ox_gas (kO)": ox_gas,
            "red_gas (kO)": red_gas,
            "nh3_gas (kO)": nh3_gas,
            "pm1 (µg/m³)": pm1,
            "pm2.5 (µg/m³)": pm2p5,
            "pm10 (µg/m³)": pm10,
        }
        writer.update(data)
        time.sleep(10)



# Exit cleanly
except KeyboardInterrupt:
    sys.exit(0)
