from modules.devices.stylusdummy import STYLUS_DUMMY_VALUES

class Device:
    def __init__(self, deviceid, name):
        self.deviceid = deviceid
        self.name = name
        self.active = False
        self.valuators = {}
        self.inactive_frames = 0

class Devices:
    def __init__(self):
        self.devices = {}
    
    def close(self):
        pass
    
    def add_device(self, namestr):
        device = Device(0, "Stylus Dummy")
        device.valuators = STYLUS_DUMMY_VALUES
        self.devices[namestr] = device
        return True

    def update_devices(self):
        pass

    def is_device_active(self, namestr):
        return True

    def get_device_values(self, namestr):
        return STYLUS_DUMMY_VALUES
