from ctypes import pointer

import Xlib
from Xlib.display import Display
from Xlib.ext import xinput

STYLUS_DUMMY_VALUES = {
    "x": 0.0,
    "y": 0.0,
    "pressure": 1.0,
    "tilt x": 0.5,
    "tilt y": 0.5,
    "wheel": 0.0
}

def convert_valuator_name(name):
    if name in ("Abs X"):
        return "x"
    elif name in ("Abs Y"):
        return "y"
    elif name in ("Abs Pressure"):
        return "pressure"
    elif name in ("Abs Tilt X"):
        return "tilt x"
    elif name in ("Abs Tilt Y"):
        return "tilt y"
    elif name in ("Abs Wheel"):
        return "wheel"
    return name

class Device:
    def __init__(self, deviceid, name):
        self.deviceid = deviceid
        self.name = name
        self.active = False
        self.valuators = {}
        self.inactive_frames = 0

    def select_events(self, window):
        xinput.select_events(window, ((self.deviceid, xinput.MotionMask),))

class Devices:
    def __init__(self):
        # init XInput
        self.display = Display()
        self.window = self.display.screen().root

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
            return False

        device = Device(dev_info["deviceid"], dev_info["name"])
        
        for c in dev_info["classes"]:
            if c["type"] == xinput.ValuatorClass:
                if c["label"] > 0:
                    valuator_name = self.display.get_atom_name(int(c["label"]))
                    device.valuators[convert_valuator_name(valuator_name)] = 0.0

        print("Found %s"%device.name)

        self.devices[namestr] = device

        return True

    def update_devices(self):
        for devicename in self.devices:
            dev = self.devices[devicename]

            dev.active = False
            dev.select_events(self.window)
            while self.display.pending_events():
                # if the stylus is sending events, consider it active.
                dev.active = True
                _ = self.display.next_event()
            
            if not dev.active:
                dev.inactive_frames += 1
                if dev.inactive_frames > 2:
                    for valname in STYLUS_DUMMY_VALUES:
                        dev.valuators[valname] = STYLUS_DUMMY_VALUES[valname]
                    return
            else: dev.inactive_frames = 0

            # then simply query the device state as I couldn't find anything like XGetEventData in the Xlib library.
            dev_info = xinput.query_device(self.display, dev.deviceid)._data["devices"][0]
            
            for c in dev_info["classes"]:
                if c["type"] == xinput.ValuatorClass:
                    valuator_name = self.display.get_atom_name(int(c["label"]))
                    dev.valuators[convert_valuator_name(valuator_name)] = (c["value"] - c["min"]) / (c["max"] - c["min"])
                    if valuator_name == "pressure":
                        print(c["value"])

    def is_device_active(self, namestr):
        if namestr not in self.devices:
            # print(f'Device "{namestr}" not found in current devices.')
            return False
        
        return self.devices[namestr].active

    def get_device_values(self, namestr):
        if namestr not in self.devices:
            # print(f'Device "{namestr}" not found in current devices.')
            return STYLUS_DUMMY_VALUES
        
        return self.devices[namestr].valuators
