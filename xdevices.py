from Xlib.display import Display
from Xlib.ext import xinput

class XDevices:
    def __init__(self):
        # init XInput
        self.display = Display()

        vers_info = self.display.xinput_query_version()
        print(f'XInput version {vers_info.major_version}.{vers_info.minor_version}')

        self.devices = {}
    
    def close(self):
        self.display.close()
    
    def add_device(self, namestr):
        devices = xinput.query_device(self.display, xinput.AllDevices)
        
        dev_info = None
        for device in devices._data["devices"]:
            if device["use"] == xinput.SlavePointer and namestr in device["name"]:
                dev_info = device

        if not dev_info:
            print(f'No device with "{namestr}" in its name was found.')
            return

        device = {
            "deviceid": dev_info["deviceid"],
            "name": dev_info["name"],
            "active": False,
            "valuators": {},
        }

        for c in dev_info["classes"]:
            if c["type"] == xinput.ValuatorClass:
                if c["label"] > 0:
                    valuator_name = self.display.get_atom_name(int(c["label"]))
                    device["valuators"][valuator_name] = 0.0

        self.devices[namestr] = device

    def update_devices(self):
        for key in self.devices:
            d = self.devices[key]
            dev_info = xinput.query_device(self.display, d["deviceid"])._data["devices"][0]
            d["active"] = True if dev_info["classes"][0]["state"][0] else False
            
            if not d["active"]:
                return
            
            for c in dev_info["classes"]:
                if c["type"] == xinput.ValuatorClass:
                    valuator_name = self.display.get_atom_name(int(c["label"]))
                    d["valuators"][valuator_name] = (c["value"] - c["min"]) / (c["max"] - c["min"])

    def is_device_active(self, namestr):
        if namestr not in self.devices:
            print(f'Device "{namestr}" not found in current devices.')
            return None
        
        return self.devices[namestr]["active"]

    def get_device_values(self, namestr):
        if namestr not in self.devices:
            print(f'Device "{namestr}" not found in current devices.')
            return None
        
        return self.devices[namestr]["valuators"]
