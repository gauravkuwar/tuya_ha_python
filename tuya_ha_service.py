"""
Tuya (Local) and Homekit integration for lights, 
with only on/off functionality.
"""

import logging
import signal
import random
import json
import tinytuya
import threading

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import CATEGORY_LIGHTBULB

logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")

with open('devices.json', 'r') as f:
    devices = json.load(f)

class LightBulb(Accessory):
    """Lightbulb integrated with Tuya devices"""

    category = CATEGORY_LIGHTBULB

    def __init__(self, dev_idx, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.i = dev_idx
        logging.info(f"Connecting to {devices[self.i]['name']} ...")
        self.tuya_dev = tinytuya.BulbDevice(
            devices[self.i]['id'], 
            devices[self.i]['ip_addr'], 
            local_key=devices[self.i]['local_key'], 
            dev_type='default')
        
        self.tuya_dev.set_socketRetryLimit(1)
        self.tuya_dev.set_socketTimeout(0.5)
        self.tuya_dev.set_version(devices[self.i]['version'])
        
        self.ha_state = 0 # get initial state from tuya
           
        # initialize homekit device
        serv_light = self.add_preload_service('Lightbulb')
        self.char_on = serv_light.configure_char(
            'On', value=self.ha_state, setter_callback=self.set_bulb)
        
        print(devices[self.i]['name'], self.ha_state)
    
    def set_bulb(self, value):
        if self.tuya_state() != "Error":
            if value: 
                self.tuya_dev.turn_on()
            else:
                self.tuya_dev.turn_off()

            self.ha_state = self.tuya_state()
            logging.info(f"{devices[self.i]['name']} value: {value}")
        else:
            self.char_on.set_value(0) 
            
    
    # only in the case lights are changed from tuya app, or other sources.
    @Accessory.run_at_interval(5)
    async def run(self):
        cur_tuya_state = self.tuya_state()
        
        if cur_tuya_state == "Error":
            self.char_on.set_value(0) 
            
        elif self.ha_state != cur_tuya_state:
            self.char_on.set_value(cur_tuya_state) 
        
    def tuya_state(self):        
        tuya_status = self.tuya_dev.status()
        if 'dps' in tuya_status:
            on_off_num = '1' if devices[self.i]['version'] == 3.1 else "20"
            return tuya_status['dps'][on_off_num]
        else:
            # we can't have the tuya app open at the same time as this service
            logging.info(f"Error in {devices[self.i]['name']}: {tuya_status}")
            return "Error" # error

def get_bridge(driver):
    bridge = Bridge(driver, 'Tuya Hub')
    for idx, dev in enumerate(devices):
        bridge.add_accessory(LightBulb(idx, driver, dev['name']))

    return bridge

# run the process
driver = AccessoryDriver(port=51826, persist_file='home.state')
driver.add_accessory(accessory=get_bridge(driver))
signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()
