from modules.devices.stylusdummy import STYLUS_DUMMY_VALUES

class Devices:
    def __init__(self):
        pass
    
    def close(self):
        pass
    
    def add_device(self, namestr):
        return False

    def update_devices(self):
        pass

    def is_device_active(self, namestr):
        return False

    def get_device_values(self, namestr):
        return STYLUS_DUMMY_VALUES

