"""
Tuya (Local) and Homekit integration for lights, 
with only on/off functionality.
"""

import logging
import signal
import random
import json
import tinytuya

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
        
        # initialize tuya device
        self.tuya_dev = tinytuya.BulbDevice(
            devices[self.i]['id'], 
            devices[self.i]['ip_addr'], 
            local_key=devices[self.i]['local_key'], 
            dev_type='default')
        
        self.tuya_dev.set_version(devices[self.i]['version'])
        
        self.ha_state = self.tuya_state() # get initial state from tuya
        
        # initialize homekit device
        serv_light = self.add_preload_service('Lightbulb')
        self.char_on = serv_light.configure_char(
            'On', value=self.ha_state, setter_callback=self.set_bulb)
    
    def set_bulb(self, value):
        if self.tuya_state() != 2:
            if value: 
                self.tuya_dev.turn_on()
            else:
                self.tuya_dev.turn_off()

            self.ha_state = self.tuya_state()
            logging.info(f"{devices[self.i]['name']} value: {value}")
    
    # only in the case lights are changed from tuya app, or other sources.
    @Accessory.run_at_interval(5)
    async def run(self):
        if self.ha_state != self.tuya_state():
            self.char_on.set_value(self.tuya_state())

    def tuya_state(self):
        tuya_status = self.tuya_dev.status()
        if 'dps' in tuya_status:
            on_off_num = '1' if devices[self.i]['version'] == 3.1 else "20"
            return tuya_status['dps'][on_off_num]
        else:
            # we can't have the tuya app open at the same time as this service
            logging.info("Error: close other tuya connections!")
            return 2 # error

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
